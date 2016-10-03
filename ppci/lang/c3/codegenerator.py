""" This module contains the code generation class. """

import logging
from ... import ir
from ... import irutils
from ...binutils import debuginfo
from . import astnodes as ast
from .scope import SemanticError


class CodeGenerator:
    """ Generates intermediate (IR) code from a package.

    The entry function is
    'genModule'. The main task of this part is to rewrite complex control
    structures, such as while and for loops into simple conditional
    jump statements. Also complex conditional statements are simplified.
    Such as 'and' and 'or' statements are rewritten in conditional jumps.
    And structured datatypes are rewritten.

    Type checking is done in one run with code generation.
    """
    logger = logging.getLogger('c3cgen')

    def __init__(self, diag, debug_db):
        self.builder = irutils.Builder()
        self.diag = diag
        self.context = None
        self.debug_db = debug_db
        self.module_ok = False

    def gencode(self, mod: ast.Module, context):
        """ Generate code for a single module """
        assert isinstance(mod, ast.Module)
        self.context = context
        self.builder.prepare()
        self.module_ok = True
        self.logger.info('Generating ir-code for %s', mod.name)
        self.builder.module = self.context.var_map[mod]

        # Only generate function if function contains a body:
        for func in mod.functions:
            if func.body:
                # Try per function, in case of error, continue with next
                try:
                    self.gen_function(func)
                except SemanticError as ex:
                    self.error(ex.msg, ex.loc)

        if not self.module_ok:
            raise SemanticError("Errors occurred", None)
        return self.builder.module

    def gen_globals(self, module, context):
        """ Generate global variables and modules """
        self.context = context
        ir_module = ir.Module(module.name)
        context.var_map[module] = ir_module

        # Generate room for global variables:
        for var in module.inner_scope.variables:
            assert not var.isLocal
            if var.ival:
                assert context.equal_types('int', var.typ)
                cval = context.eval_const(var.ival)
                cval = context.pack_int(cval)
            else:
                cval = None
            ir_var = ir.Variable(
                var.name, context.size_of(var.typ), value=cval)
            context.var_map[var] = ir_var
            ir_module.add_variable(ir_var)

            # Create debug infos:
            dbg_typ = self.get_debug_type(var.typ)
            dv = debuginfo.DebugVariable(var.name, dbg_typ, var.loc)
            self.debug_db.enter(ir_var, dv)

    def emit(self, instruction, loc=None):
        """
            Emits the given instruction to the builder.
            Can be muted for constants.
        """
        self.builder.emit(instruction)
        if loc:
            self.debug_db.enter(instruction, debuginfo.DebugLocation(loc))
        return instruction

    def get_debug_type(self, typ):
        """ Get or create debug type info in the debug information """
        # Lookup the type:
        typ = self.context.get_type(typ)

        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        if isinstance(typ, ast.BaseType):
            dbg_typ = debuginfo.DebugBaseType(
                typ.name, self.context.size_of(typ), 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, ast.PointerType):
            ptype = self.get_debug_type(typ.ptype)
            dbg_typ = debuginfo.DebugPointerType(ptype)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, ast.StructureType):
            dbg_typ = debuginfo.DebugStructType()

            # Enter the type here, so the cached value is taken when
            # a linked list is encountered:
            self.debug_db.enter(typ, dbg_typ)
            for field in typ.fields:
                offset = field.offset
                field_typ = self.get_debug_type(field.typ)
                dbg_typ.add_field(field.name, field_typ, offset)
        elif isinstance(typ, ast.ArrayType):
            et = self.get_debug_type(typ.element_type)
            if isinstance(typ.size, int):
                size = typ.size
            else:
                size = self.context.eval_const(typ.size)
            dbg_typ = debuginfo.DebugArrayType(et, size)
            self.debug_db.enter(typ, dbg_typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return dbg_typ

    def error(self, msg, loc=None):
        """ Emit error to diagnostic system and mark package as invalid """
        self.module_ok = False
        self.diag.error(msg, loc)

    def gen_function(self, function):
        """ Generate code for a function. This involves creating room
            for parameters on the stack, and generating code for the function
            body.
        """
        if self.context.equal_types('void', function.typ.returntype):
            ir_function = self.builder.new_procedure(function.name)
        else:
            return_type = self.get_ir_type(function.typ.returntype)
            ir_function = self.builder.new_function(function.name, return_type)
        dfi = debuginfo.DebugFunction(function.name, function.loc)
        self.debug_db.enter(ir_function, dfi)
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # generate parameters:
        param_map = {}
        for param in function.parameters:
            # Parameters can only be simple types (pass by value)
            param_ir_typ = self.get_ir_type(param.typ)

            # Define parameter for function:
            ir_parameter = ir.Parameter(param.name, param_ir_typ)
            ir_function.add_parameter(ir_parameter)
            param_map[param] = ir_parameter

            # Debug info:
            dbg_typ = self.get_debug_type(param.typ)
            # self.debug_info.enter(ir_parameter, DebugVariable(
            #    param.name, dbg_typ, param.loc))
            # TODO: do something with parameters

        # generate room for locals:
        for sym in function.inner_scope:
            var_name = 'var_{}'.format(sym.name)
            variable = ir.Alloc(var_name, self.context.size_of(sym.typ))
            self.emit(variable)
            if sym.isParameter:
                # Get the parameter from earlier:
                parameter = param_map[sym]

                # For paramaters, allocate space and copy the value into
                # memory. Later, the mem2reg pass will extract these values.
                # Move parameter into local copy:
                self.emit(ir.Store(parameter, variable))
            elif isinstance(sym, ast.Variable):
                pass
            else:  # pragma: no cover
                raise NotImplementedError(str(sym))
            self.context.var_map[sym] = variable

            # Debug info:
            dbg_typ = self.get_debug_type(sym.typ)
            dv = debuginfo.DebugVariable(sym.name, dbg_typ, sym.loc)
            self.debug_db.enter(variable, dv)
            dfi.add_variable(dv)

        # Generate code for body:
        self.gen_stmt(function.body)

        # Close block:
        if not self.builder.block.is_closed:
            # In case of void function, introduce exit instruction:
            if self.context.equal_types('void', function.typ.returntype):
                self.emit(ir.Exit())
            else:
                if self.builder.block.is_empty:
                    last_block = self.builder.block
                    self.builder.set_block(None)
                    ir_function.delete_unreachable()
                    assert not last_block.is_used
                    assert last_block not in ir_function
                else:
                    raise SemanticError(
                        'Function does not return a value', function.loc)

        # Remove unreachable blocks from the function:
        ir_function.delete_unreachable()
        self.builder.set_function(None)

    def get_ir_int(self):
        mapping = {1: ir.i8, 2: ir.i16, 4: ir.i32, 8: ir.i64}
        return mapping[self.context.get_type('int').byte_size]

    def get_ir_type(self, cty):
        """ Given a certain type, get the corresponding ir-type """
        cty = self.context.get_type(cty)
        if self.context.equal_types(cty, 'int'):
            return self.get_ir_int()
        elif self.context.equal_types(cty, 'double'):
            return ir.f64
        elif self.context.equal_types(cty, 'float'):
            return ir.f32
        elif self.context.equal_types(cty, 'void'):  # pragma: no cover
            raise RuntimeError('Cannot get void type')
        elif self.context.equal_types(cty, 'bool'):
            # Implement booleans as integers:
            return self.get_ir_int()
        elif self.context.equal_types(cty, 'byte'):
            return ir.i8
        elif isinstance(cty, ast.PointerType):
            return ir.ptr
        else:  # pragma: no cover
            raise NotImplementedError(str(cty))

    def gen_stmt(self, code: ast.Statement):
        """ Generate code for a statement """
        try:
            assert isinstance(code, ast.Statement)
            if isinstance(code, ast.Compound):
                for statement in code.statements:
                    self.gen_stmt(statement)
            elif isinstance(code, ast.Empty):
                pass
            elif isinstance(code, ast.Assignment):
                self.gen_assignment_stmt(code)
            elif isinstance(code, ast.ExpressionStatement):
                # This must be always a void function call
                assert isinstance(code.ex, ast.FunctionCall)
                value = self.gen_function_call(code.ex)
                assert self.context.equal_types('void', code.ex.typ)
                assert value is None
            elif isinstance(code, ast.If):
                self.gen_if_stmt(code)
            elif isinstance(code, ast.Return):
                self.gen_return_stmt(code)
            elif isinstance(code, ast.While):
                self.gen_while(code)
            elif isinstance(code, ast.For):
                self.gen_for_stmt(code)
            elif isinstance(code, ast.Switch):
                self.gen_switch_stmt(code)
            else:  # pragma: no cover
                raise NotImplementedError(str(code))
        except SemanticError as exc:
            self.error(exc.msg, exc.loc)

    def gen_return_stmt(self, code):
        """ Generate code for return statement """
        if code.expr:
            ret_val = self.gen_expr_code(code.expr, rvalue=True)
            self.emit(ir.Return(ret_val))
        else:
            self.emit(ir.Exit())
        self.builder.set_block(self.builder.new_block())

    def gen_assignment_stmt(self, code):
        """ Generate code for assignment statement """
        # Evaluate left hand side:
        lval = self.gen_expr_code(code.lval)

        # Check that the left hand side is a simple type:
        assert self.context.is_simple_type(code.lval.typ)

        # Check that left hand is an lvalue:
        assert code.lval.lvalue

        # Evaluate right hand side (and make it rightly typed):
        rval = self.gen_expr_code(code.rval, rvalue=True)
        assert self.context.equal_types(code.lval.typ, code.rval.typ)

        # Implement short hands (+=, -= etc):
        if code.is_shorthand:
            # In case of '+=', evaluate the left hand side once, and use
            # the value twice. Once as an lvalue, once as rvalue.
            # Determine loaded type:
            load_ty = self.get_ir_type(code.lval.typ)

            # We know, the left hand side is an lvalue, so load it:
            lhs_ld = self.emit(
                ir.Load(lval, 'assign_op_load', load_ty), loc=code.loc)

            # Now construct the rvalue:
            oper = code.shorthand_operator
            rval = self.emit(
                ir.Binop(lhs_ld, oper, rval, "binop", rval.ty), loc=code.loc)

        # Determine volatile property from left-hand-side type:
        volatile = code.lval.typ.volatile
        return self.emit(ir.Store(rval, lval, volatile=volatile), loc=code.loc)

    def gen_if_stmt(self, code):
        """ Generate code for if statement """
        true_block = self.builder.new_block()
        false_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_cond_code(code.condition, true_block, false_block)
        self.builder.set_block(true_block)
        self.gen_stmt(code.truestatement)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(false_block)
        self.gen_stmt(code.falsestatement)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)

    def gen_while(self, code):
        """ Generate code for while statement """
        main_block = self.builder.new_block()
        test_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.emit(ir.Jump(test_block))
        self.builder.set_block(test_block)
        self.gen_cond_code(code.condition, main_block, final_block)
        self.builder.set_block(main_block)
        self.gen_stmt(code.statement)
        self.emit(ir.Jump(test_block))
        self.builder.set_block(final_block)

    def gen_for_stmt(self, code):
        """ Generate for-loop code """
        main_block = self.builder.new_block()
        test_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_stmt(code.init)
        self.emit(ir.Jump(test_block))
        self.builder.set_block(test_block)
        self.gen_cond_code(code.condition, main_block, final_block)
        self.builder.set_block(main_block)
        self.gen_stmt(code.statement)
        self.gen_stmt(code.final)
        self.emit(ir.Jump(test_block))
        self.builder.set_block(final_block)

    def gen_switch_stmt(self, switch):
        """ Generate code for a switch statement """
        ir_val = self.gen_expr_code(switch.expression, rvalue=True)
        assert self.context.equal_types('int', switch.expression.typ)

        final_block = self.builder.new_block()
        test_block = self.builder.new_block()
        self.emit(ir.Jump(test_block))

        def_block = None
        # Generate code in linear way:
        for option_val, option_code in switch.options:
            # Generate code for case:
            code_block = self.builder.new_block()
            self.builder.set_block(code_block)
            self.gen_stmt(option_code)
            self.emit(ir.Jump(final_block))

            if option_val is None:
                # default case
                def_block = code_block
            else:
                # TODO: type check constant:
                loc = option_val.loc
                self.builder.set_block(test_block)
                o_val = self.context.eval_const(option_val)
                ir_val2 = self.emit(ir.Const(
                    o_val, 'cmpval', self.get_ir_int()), loc=loc)
                tb2 = self.builder.new_block()
                self.emit(
                    ir.CJump(ir_val, '==', ir_val2, code_block, tb2), loc=loc)
                test_block = tb2

        self.builder.set_block(test_block)
        assert def_block
        self.emit(ir.Jump(def_block))
        self.builder.set_block(final_block)

    def gen_cond_code(self, expr, bbtrue, bbfalse):
        """ Generate conditional logic.
            Implement sequential logical operators. """
        if isinstance(expr, ast.Binop):
            if expr.op == 'or':
                # Implement sequential logic:
                second_block = self.builder.new_block()
                self.gen_cond_code(expr.a, bbtrue, second_block)
                self.builder.set_block(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op == 'and':
                # Implement sequential logic:
                second_block = self.builder.new_block()
                self.gen_cond_code(expr.a, second_block, bbfalse)
                self.builder.set_block(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op in ['==', '>', '<', '!=', '<=', '>=']:
                lhs = self.gen_expr_code(expr.a, rvalue=True)
                rhs = self.gen_expr_code(expr.b, rvalue=True)
                self.context.equal_types(expr.a.typ, expr.b.typ)
                self.emit(
                    ir.CJump(lhs, expr.op, rhs, bbtrue, bbfalse), loc=expr.loc)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, ast.Literal):
            self.gen_expr_code(expr)
            if expr.val:
                self.emit(ir.Jump(bbtrue), loc=expr.loc)
            else:
                self.emit(ir.Jump(bbfalse), loc=expr.loc)
        elif isinstance(expr, ast.Unop) and expr.op == 'not':
            # In case of not, simply swap true and false!
            self.gen_cond_code(expr.a, bbfalse, bbtrue)
        elif isinstance(expr, ast.Expression):
            # Evaluate expression, make sure it is boolean and compare it
            # with true:
            value = self.gen_expr_code(expr, rvalue=True)
            assert self.context.equal_types(expr.typ, 'bool')
            true_val = self.emit(
                ir.Const(1, "true", self.get_ir_type(expr.typ)))
            self.emit(ir.CJump(value, '==', true_val, bbtrue, bbfalse))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check that the condition is a boolean value:
        assert self.context.equal_types(expr.typ, 'bool')

    def gen_expr_code(self, expr: ast.Expression, rvalue=False) -> ir.Value:
        """ Generate code for an expression. Return the generated ir-value """
        assert isinstance(expr, ast.Expression)
        if expr.is_bool:
            value = self.gen_bool_expr(expr)
        else:
            if isinstance(expr, ast.Binop):
                value = self.gen_binop(expr)
            elif isinstance(expr, ast.Unop):
                value = self.gen_unop(expr)
            elif isinstance(expr, ast.Identifier):
                value = self.gen_identifier(expr)
            elif isinstance(expr, ast.Deref):
                value = self.gen_dereference(expr)
            elif isinstance(expr, ast.Member):
                value = self.gen_member_expr(expr)
            elif isinstance(expr, ast.Index):
                value = self.gen_index_expr(expr)
            elif isinstance(expr, ast.Literal):
                value = self.gen_literal_expr(expr)
            elif isinstance(expr, ast.TypeCast):
                value = self.gen_type_cast(expr)
            elif isinstance(expr, ast.Sizeof):
                value = self.gen_sizeof(expr)
            elif isinstance(expr, ast.FunctionCall):
                value = self.gen_function_call(expr)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))

        assert isinstance(value, ir.Value)

        # do rvalue trick here, create a r-value when required:
        if rvalue and expr.lvalue:
            # Generate expression code and insert an extra load instruction
            # when required.
            # This means that the value can be used in an expression or as
            # a parameter.

            val_typ = self.context.get_type(expr.typ)
            assert isinstance(val_typ, (ast.PointerType, ast.BaseType))

            # Determine loaded type:
            load_ty = self.get_ir_type(expr.typ)

            # Load the value:
            value = self.emit(ir.Load(value, 'load', load_ty), loc=expr.loc)

            # This expression is no longer an lvalue
            expr.lvalue = False
        return value

    def gen_sizeof(self, expr):
        # This is not a location value..
        expr.lvalue = False

        type_size = self.context.size_of(expr.query_typ)
        return self.emit(
            ir.Const(type_size, 'sizeof', self.get_ir_int()), loc=expr.loc)

    def gen_dereference(self, expr: ast.Deref):
        """ dereference pointer type, which means *(expr) """
        assert isinstance(expr, ast.Deref)

        # Make sure to have the rvalue of the pointer:
        deref_value = self.gen_expr_code(expr.ptr, rvalue=True)

        # A pointer is always a lvalue:
        expr.lvalue = True

        ptr_typ = self.context.get_type(expr.ptr.typ)
        assert isinstance(ptr_typ, ast.PointerType)
        return deref_value

    def gen_unop(self, expr):
        """ Generate code for unary operator """
        if expr.op == '&':
            rhs = self.gen_expr_code(expr.a)
            assert expr.a.lvalue
            expr.lvalue = False
            return rhs
        elif expr.op == '+':
            rhs = self.gen_expr_code(expr.a, rvalue=True)
            expr.lvalue = False
            return rhs
        elif expr.op == '-':
            rhs = self.gen_expr_code(expr.a, rvalue=True)
            expr.lvalue = False

            # Implement unary operator with sneaky trick using 0 - v binop:
            zero = self.emit(ir.Const(0, 'zero', rhs.ty))
            return self.emit(ir.Binop(zero, '-', rhs, 'unary_minus', rhs.ty))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))

    def gen_bool_expr(self, expr):
        """ Generate code for cases where a boolean value is assigned """
        # In case of boolean assignment like:
        # 'var bool x = true or false;'

        # Use condition machinery:
        true_block = self.builder.new_block()
        false_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_cond_code(expr, true_block, false_block)

        # True path:
        self.builder.set_block(true_block)
        true_val = self.emit(
            ir.Const(1, 'true', self.get_ir_type(expr.typ)))
        self.emit(ir.Jump(final_block))

        # False path:
        self.builder.set_block(false_block)
        false_val = self.emit(
            ir.Const(0, 'false', self.get_ir_type(expr.typ)))
        self.emit(ir.Jump(final_block))

        # Final path:
        self.builder.set_block(final_block)
        phi = self.emit(
            ir.Phi('bool_res', self.get_ir_type(expr.typ)))
        phi.set_incoming(false_block, false_val)
        phi.set_incoming(true_block, true_val)

        # This is for sure no lvalue:
        expr.lvalue = False
        return phi

    def gen_binop(self, expr: ast.Binop):
        """ Generate code for binary operation """
        assert isinstance(expr, ast.Binop)
        assert expr.op not in ast.Binop.cond_ops
        expr.lvalue = False

        # Dealing with simple arithmatic
        a_val = self.gen_expr_code(expr.a, rvalue=True)
        b_val = self.gen_expr_code(expr.b, rvalue=True)
        assert isinstance(a_val, ir.Value)
        assert isinstance(b_val, ir.Value)

        self.context.equal_types(expr.a.typ, expr.b.typ)

        return self.emit(
            ir.Binop(a_val, expr.op, b_val, "binop", a_val.ty), loc=expr.loc)

    def gen_identifier(self, expr):
        """ Generate code for when an identifier was referenced """
        # Generate code for this identifier.
        target = self.context.resolve_symbol(expr)

        # This returns the dereferenced variable.
        if isinstance(target, ast.Variable):
            expr.lvalue = True
            value = self.context.var_map[target]
        elif isinstance(target, ast.Constant):
            expr.lvalue = False
            c_val = self.context.get_constant_value(target)
            c_typ = self.get_ir_type(target.typ)
            value = self.emit(ir.Const(c_val, target.name, c_typ))
        else:  # pragma: no cover
            raise NotImplementedError(str(target))
        return value

    def is_module_ref(self, expr):
        """ Determine whether a module is referenced """
        if isinstance(expr, ast.Member):
            if isinstance(expr.base, ast.Identifier):
                target = self.context.resolve_symbol(expr.base)
                return isinstance(target, ast.Module)
            elif isinstance(expr, ast.Member):
                return self.is_module_ref(expr.base)
        return False

    def gen_member_expr(self, expr):
        """ Generate code for member expression such as struc.mem = 2
            This could also be a module deref!
        """
        if self.is_module_ref(expr):
            # Damn, we are referring something inside another module!
            # Invoke scope machinery!
            target = self.context.resolve_symbol(expr)
            if isinstance(target, ast.Variable):
                expr.lvalue = True
                value = self.context.var_map[target]
            else:  # pragma: no cover
                raise NotImplementedError(str(target))
            return value

        base = self.gen_expr_code(expr.base)

        # The base is a valid expression:
        assert isinstance(base, ir.Value)
        expr.lvalue = expr.base.lvalue
        basetype = self.context.get_type(expr.base.typ)
        assert isinstance(basetype, ast.StructureType)
        assert basetype.has_field(expr.field)

        # expr must be lvalue because we handle with addresses of variables
        assert expr.lvalue

        # Calculate offset into struct:
        base_type = self.context.get_type(expr.base.typ)
        offset = self.emit(
            ir.Const(base_type.field_offset(expr.field), 'offset', ir.ptr))

        # Calculate memory address of field:
        return self.emit(ir.add(base, offset, "mem_addr", ir.ptr))

    def gen_index_expr(self, expr):
        """ Array indexing """
        base = self.gen_expr_code(expr.base)
        idx = self.gen_expr_code(expr.i, rvalue=True)

        base_typ = self.context.get_type(expr.base.typ)
        assert isinstance(base_typ, ast.ArrayType)

        # Make sure the index is an integer:
        assert self.context.equal_types('int', expr.i.typ)

        # Base address must be a location value:
        assert expr.base.lvalue
        element_type = self.context.get_type(base_typ.element_type)
        element_size = self.context.size_of(element_type)
        expr.lvalue = True

        int_ir_type = self.get_ir_type('int')

        # Generate constant:
        e_size = self.emit(ir.Const(element_size, 'element_size', int_ir_type))

        # Calculate offset:
        offset = self.emit(
            ir.mul(idx, e_size, "element_offset", int_ir_type), loc=expr.loc)
        offset = self.emit(ir.to_ptr(offset, 'elem_offset'), loc=expr.loc)

        # Calculate address:
        return self.emit(
            ir.add(base, offset, "element_address", ir.ptr), loc=expr.loc)

    def gen_literal_expr(self, expr):
        """ Generate code for literal """
        expr.lvalue = False

        # Construct correct const value:
        if isinstance(expr.val, str):
            cval = self.context.pack_string(expr.val)
            value = ir.LiteralData(cval, 'strval')
        elif isinstance(expr.val, int):  # boolean is a subclass of int!
            # For booleans, use the integer as storage class:
            val = int(expr.val)
            value = ir.Const(val, 'cnst', self.get_ir_int())
        elif isinstance(expr.val, float):
            val = float(expr.val)
            value = ir.Const(val, 'cnst', ir.f64)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.val))
        return self.emit(value)

    def gen_type_cast(self, expr):
        """ Generate code for type casting """
        # When type casting, the rvalue property is lost.
        ar = self.gen_expr_code(expr.a, rvalue=True)
        expr.lvalue = False

        from_type = self.context.get_type(expr.a.typ)
        to_type = self.context.get_type(expr.to_type)
        # 0 = not possible
        # 1 = possible
        # 2 = automatic

        cast_map = {
            'byte': {
                'byte': 1,
            },
            'int': {
                'byte': 1,
                'int': 1,
                'float': 1,
            },
            'float': {
                'byte': 1,
                'int': 1,
                'float': 1,
            }
        }

        if isinstance(from_type, ast.PointerType) and \
                isinstance(to_type, ast.PointerType):
            return ar
        elif self.context.equal_types('int', from_type) and \
                isinstance(to_type, ast.PointerType):
            return self.emit(ir.to_ptr(ar, 'int2ptr'))
        elif self.context.equal_types('int', to_type) \
                and isinstance(from_type, ast.PointerType):
            return self.emit(ir.Cast(ar, 'ptr2int', self.get_ir_int()))
        elif isinstance(from_type, ast.BaseType) \
                and from_type.name == 'byte' and \
                isinstance(to_type, ast.BaseType) and to_type.name == 'int':
            return self.emit(ir.Cast(ar, 'byte2int', self.get_ir_int()))
        elif isinstance(from_type, ast.BaseType) \
                and from_type.name == 'int' and \
                isinstance(to_type, ast.BaseType) and to_type.name == 'byte':
            return self.emit(ir.to_i8(ar, 'bytecast'))
        elif self.context.equal_types('float', to_type) \
                and self.context.equal_types('int', from_type):
            return self.emit(ir.Cast(ar, 'int2flt', self.get_ir_type('float')))
        elif self.context.equal_types('float', to_type) \
                and self.context.equal_types('double', from_type):
            return self.emit(ir.Cast(ar, 'dbl2flt', self.get_ir_type('float')))
        elif self.context.equal_types('double', to_type) \
                and self.context.equal_types('float', from_type):
            return self.emit(
                ir.Cast(ar, 'flt2dbl', self.get_ir_type('double')))
        else:  # pragma: no cover
            raise NotImplementedError(
                'Cannot cast {} to {}'.format(from_type, to_type))

    def gen_function_call(self, expr):
        """ Generate code for a function call """
        # Lookup the function in question:
        target_func = self.context.resolve_symbol(expr.proc)
        assert isinstance(target_func, ast.Function)
        ftyp = target_func.typ
        fname = target_func.package.name + '_' + target_func.name

        # Check arguments:
        ptypes = ftyp.parametertypes
        assert len(expr.args) == len(ptypes)

        # Evaluate the arguments:
        args = []
        for arg_expr, arg_typ in zip(expr.args, ptypes):
            arg_val = self.gen_expr_code(arg_expr, rvalue=True)
            self.context.equal_types(arg_expr.typ, arg_typ)
            args.append(arg_val)

        # Return type will never be an lvalue:
        expr.lvalue = False

        assert self.context.is_simple_type(ftyp.returntype)

        if self.context.equal_types(expr.typ, 'void'):
            self.emit(ir.ProcedureCall(fname, args), loc=expr.loc)
        else:
            # Determine return type:
            ret_typ = self.get_ir_type(expr.typ)

            # Emit call:
            return self.emit(
                ir.FunctionCall(fname, args, fname + '_rv', ret_typ),
                loc=expr.loc)
