"""
    This module contains the code generation class.
"""

import logging
import struct
from ... import ir
from ... import irutils
from ...binutils.debuginfo import DebugLocation, DebugFunction
from ...binutils.debuginfo import DebugBaseType, DebugStructType
from ...binutils.debuginfo import DebugPointerType, DebugArrayType
from ...binutils.debuginfo import DebugVariable
from . import astnodes as ast
from .scope import SemanticError


def pack_string(txt, context):
    """ Pack a string using 4 bytes length followed by text data """
    mapping = {1: '<B', 2: '<H', 4: '<I', 8: '<Q'}
    fmt = mapping[context.get_type('int').byte_size]
    length = struct.pack(fmt, len(txt))
    data = txt.encode('ascii')
    return length + data


class CodeGenerator:
    """
      Generates intermediate (IR) code from a package. The entry function is
      'genModule'. The main task of this part is to rewrite complex control
      structures, such as while and for loops into simple conditional
      jump statements. Also complex conditional statements are simplified.
      Such as 'and' and 'or' statements are rewritten in conditional jumps.
      And structured datatypes are rewritten.

      Type checking is done in one run with code generation.
    """
    def __init__(self, diag, debug_db):
        self.logger = logging.getLogger('c3cgen')
        self.builder = irutils.Builder()
        self.diag = diag
        self.context = None
        self.debug_db = debug_db
        self.module_ok = False

    def gencode(self, mod, context):
        """ Generate code for a single module """
        assert isinstance(mod, ast.Module)
        self.context = context
        self.builder.prepare()
        self.module_ok = True
        self.logger.info('Generating ir-code for %s', mod.name)
        self.builder.module = self.context.var_map[mod]
        try:
            # Check defined types of this module:
            for typ in mod.types:
                self.context.check_type(typ)

            # Only generate function if function contains a body:
            for func in mod.functions:
                if func.body:
                    # Try per function, in case of error, continue with next
                    try:
                        self.gen_function(func)
                    except SemanticError as ex:
                        self.error(ex.msg, ex.loc)
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
            ir_var = ir.Variable(var.name, context.size_of(var.typ))
            context.var_map[var] = ir_var
            assert not var.isLocal
            assert not var.ival
            ir_module.add_variable(ir_var)

            # Create debug infos:
            dbg_typ = self.get_debug_type(var.typ)
            dv = DebugVariable(var.name, dbg_typ, var.loc)
            dv.scope = 'global'
            self.debug_db.enter(ir_var, dv)

    def emit(self, instruction, loc=None):
        """
            Emits the given instruction to the builder.
            Can be muted for constants.
        """
        self.builder.emit(instruction)
        if loc:
            self.debug_db.enter(instruction, DebugLocation(loc))
        return instruction

    def get_debug_type(self, typ):
        """ Get or create debug type info in the debug information """
        # Lookup the type:
        typ = self.context.the_type(typ)

        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        # print(typ)
        name = 'type' + str(id(typ))
        if isinstance(typ, ast.BaseType):
            dbg_typ = DebugBaseType(typ.name, self.context.size_of(typ), 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, ast.PointerType):
            ptype = self.get_debug_type(typ.ptype)
            dbg_typ = DebugPointerType(name, ptype)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, ast.StructureType):
            # context.check_type(typ)
            dbg_typ = DebugStructType(name)
            self.context.check_type(typ)
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
            dbg_typ = DebugArrayType(name, et, size)
            self.debug_db.enter(typ, dbg_typ)
        else:
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
        ir_function = self.builder.new_function(function.name)
        dfi = DebugFunction(function.name, function.loc)
        self.debug_db.enter(ir_function, dfi)
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.emit(ir.Jump(first_block))
        self.builder.set_block(first_block)

        # generate parameters:
        param_map = {}
        for param in function.parameters:
            self.context.check_type(param.typ)

            # Parameters can only be simple types (pass by value)
            param_ir_typ = self.get_ir_type(param.typ, param.loc)

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
            self.context.check_type(sym.typ)
            var_name = 'var_{}'.format(sym.name)
            variable = ir.Alloc(
                var_name, self.context.size_of(sym.typ), loc=sym.loc)
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
            dv = DebugVariable(sym.name, dbg_typ, variable.loc)
            dv.scope = 'local'
            self.debug_db.enter(variable, dv)
            dfi.add_variable(dv)

        self.gen_stmt(function.body)
        self.emit(ir.Jump(ir_function.epilog))
        self.builder.set_function(None)

    def get_expr_ir_type(self, expr):
        """ Get the ir-type for an expression """
        return self.get_ir_type(expr.typ, expr.loc)

    def get_ir_int(self):
        mapping = {1: ir.i8, 2: ir.i16, 4: ir.i32, 8: ir.i64}
        return mapping[self.context.get_type('int').byte_size]

    def get_ir_type(self, cty, loc):
        """ Given a certain type, get the corresponding ir-type """
        cty = self.context.the_type(cty)
        if self.context.equal_types(cty, 'int'):
            return self.get_ir_int()
        elif self.context.equal_types(cty, 'double'):
            return ir.f64
        elif self.context.equal_types(cty, 'void'):
            # TODO: how to handle void?
            return ir.ptr
        elif self.context.equal_types(cty, 'bool'):
            # Implement booleans as integers:
            return self.get_ir_int()
        elif self.context.equal_types(cty, 'byte'):
            return ir.i8
        elif isinstance(cty, ast.PointerType):
            return ir.ptr
        else:
            raise SemanticError(
                'Cannot determine the type for "{}"'.format(cty), loc)

    def gen_stmt(self, code):
        """ Generate code for a statement """
        try:
            assert isinstance(code, ast.Statement)
            self.builder.set_loc(code.loc)
            if isinstance(code, ast.Compound):
                for statement in code.statements:
                    self.gen_stmt(statement)
            elif isinstance(code, ast.Empty):
                pass
            elif isinstance(code, ast.Assignment):
                self.gen_assignment_stmt(code)
            elif isinstance(code, ast.ExpressionStatement):
                self.gen_expr_code(code.ex)
                # Check that this is always a void function call
                if not isinstance(code.ex, ast.FunctionCall):
                    raise SemanticError('Not a call expression', code.ex.loc)
                if not self.context.equal_types('void', code.ex.typ):
                    raise SemanticError(
                        'Can only call void functions', code.ex.loc)
            elif isinstance(code, ast.If):
                self.gen_if_stmt(code)
            elif isinstance(code, ast.Return):
                self.gen_return_stmt(code)
            elif isinstance(code, ast.While):
                self.gen_while(code)
            elif isinstance(code, ast.For):
                self.gen_for_stmt(code)
            else:  # pragma: no cover
                raise NotImplementedError(str(code))
        except SemanticError as exc:
            self.error(exc.msg, exc.loc)

    def gen_return_stmt(self, code):
        """ Generate code for return statement """
        ret_val = self.gen_expr_code(code.expr, rvalue=True)
        self.emit(ir.Return(ret_val))
        self.builder.set_block(self.builder.new_block())

    def do_coerce(self, ir_val, typ, wanted_typ, loc):
        """ Try to convert expression into the given type
            ir_val: the value to convert
            typ: the type of the value
            wanted_typ: the type that it must be
            loc: the location where this is needed.
            Raises an error is the conversion cannot be done.
        """
        if self.context.equal_types(typ, wanted_typ):
            # no cast required
            return ir_val
        elif isinstance(wanted_typ, ast.PointerType) and \
                isinstance(typ, ast.PointerType):
            # Pointers are pointers, no matter the pointed data.
            return ir_val
        elif self.context.equal_types('int', typ) and \
                isinstance(wanted_typ, ast.PointerType):
            return self.emit(ir.to_ptr(ir_val, 'coerce'))
        elif self.context.equal_types('int', typ) and \
                self.context.equal_types('byte', wanted_typ):
            return self.emit(ir.to_i8(ir_val, 'coerce'))
        elif self.context.equal_types('byte', typ) and \
                self.context.equal_types('int', wanted_typ):
            return self.emit(ir.Cast(ir_val, 'coerce', self.get_ir_int()))
        else:
            raise SemanticError(
                "Cannot use '{}' as '{}'".format(typ, wanted_typ), loc)

    def is_simple_type(self, typ):
        """ Determines if the given type is a simple type """
        typ = self.context.the_type(typ)
        return isinstance(typ, ast.PointerType) or \
            isinstance(typ, ast.BaseType)

    def gen_assignment_stmt(self, code):
        """ Generate code for assignment statement """
        # Evaluate left hand side:
        lval = self.gen_expr_code(code.lval)

        # Check that the left hand side is a simple type:
        if not self.is_simple_type(code.lval.typ):
            raise SemanticError(
                'Cannot assign to complex type {}'.format(code.lval.typ),
                code.loc)

        # Check that left hand is an lvalue:
        if not code.lval.lvalue:
            raise SemanticError(
                'No valid lvalue {}'.format(code.lval), code.lval.loc)

        # Evaluate right hand side (and make it rightly typed):
        rval = self.gen_expr_code(code.rval, rvalue=True)
        rval = self.do_coerce(rval, code.rval.typ, code.lval.typ, code.loc)

        # Implement short hands (+=, -= etc):
        if code.is_shorthand:
            # In case of '+=', evaluate the left hand side once, and use
            # the value twice. Once as an lvalue, once as rvalue.
            # Determine loaded type:
            load_ty = self.get_ir_type(code.lval.typ, code.lval.loc)

            # We know, the left hand side is an lvalue, so load it:
            lhs_ld = self.emit(
                ir.Load(lval, 'assign_op_load', load_ty),
                loc=code.loc)

            # Now construct the rvalue:
            oper = code.shorthand_operator
            rval = self.emit(
                ir.Binop(lhs_ld, oper, rval, "binop", rval.ty),
                loc=code.loc)

        # Determine volatile property from left-hand-side type:
        volatile = code.lval.typ.volatile
        return self.emit(
            ir.Store(rval, lval, volatile=volatile),
            loc=code.loc)

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
                if not self.context.equal_types(expr.a.typ, expr.b.typ):
                    raise SemanticError('Types unequal {} != {}'
                                        .format(expr.a.typ, expr.b.typ),
                                        expr.loc)
                self.emit(
                    ir.CJump(lhs, expr.op, rhs, bbtrue, bbfalse), loc=expr.loc)
            else:
                raise SemanticError('non-bool: {}'.format(expr.op), expr.loc)
            expr.typ = self.context.get_type('bool')
        elif isinstance(expr, ast.Literal):
            self.gen_expr_code(expr)
            if expr.val:
                self.emit(ir.Jump(bbtrue), loc=expr.loc)
            else:
                self.emit(ir.Jump(bbfalse), loc=expr.loc)
        elif isinstance(expr, ast.Unop) and expr.op == 'not':
            # In case of not, simply swap true and false!
            self.gen_cond_code(expr.a, bbfalse, bbtrue)
            expr.typ = self.context.get_type('bool')
        elif isinstance(expr, ast.Expression):
            # Evaluate expression, make sure it is boolean and compare it
            # with true:
            value = self.gen_expr_code(expr, rvalue=True)
            if not self.context.equal_types(expr.typ, 'bool'):
                self.error('Condition must be boolean', expr.loc)
            true_val = self.emit(
                ir.Const(1, "true", self.get_expr_ir_type(expr)))
            self.emit(ir.CJump(value, '==', true_val, bbtrue, bbfalse))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check that the condition is a boolean value:
        if not self.context.equal_types(expr.typ, 'bool'):
            self.error('Condition must be boolean', expr.loc)

    def gen_expr_code(self, expr, rvalue=False):
        """ Generate code for an expression. Return the generated ir-value """
        assert isinstance(expr, ast.Expression)
        if self.is_bool(expr):
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

            # Determine loaded type:
            load_ty = self.get_ir_type(expr.typ, expr.loc)

            # Load the value:
            value = self.emit(
                ir.Load(value, 'loaded', load_ty), loc=expr.loc)

            # This expression is no longer an lvalue
            expr.lvalue = False
        return value

    def gen_sizeof(self, expr):
        # This is not a location value..
        expr.lvalue = False

        # The type of this expression is int:
        expr.typ = self.context.get_type('int')

        self.context.check_type(expr.query_typ)
        type_size = self.context.size_of(expr.query_typ)
        return self.emit(
            ir.Const(type_size, 'sizeof', self.get_ir_int()), loc=expr.loc)

    def gen_dereference(self, expr):
        """ dereference pointer type, which means *(expr) """
        assert isinstance(expr, ast.Deref)
        addr = self.gen_expr_code(expr.ptr)
        ptr_typ = self.context.the_type(expr.ptr.typ)
        expr.lvalue = True
        if not isinstance(ptr_typ, ast.PointerType):
            raise SemanticError('Cannot deref non-pointer', expr.loc)
        expr.typ = ptr_typ.ptype
        # TODO: why not load the pointed to type?

        # Determine when to introduce an extra load operation.
        # Possibly when the pointed to expression is an lvalue already?
        # TODO: re-cat this mind-melting mess into logical sense
        if expr.ptr.lvalue:
            load_ty = self.get_ir_type(ptr_typ, expr.loc)
            deref_value = self.emit(
                ir.Load(addr, 'deref', load_ty), loc=expr.loc)
        else:
            deref_value = addr
        return deref_value

    def gen_unop(self, expr):
        """ Generate code for unary operator """
        if expr.op == '&':
            rhs = self.gen_expr_code(expr.a)
            if not expr.a.lvalue:
                raise SemanticError('No valid lvalue', expr.a.loc)
            expr.typ = ast.PointerType(expr.a.typ)
            expr.lvalue = False
            return rhs
        elif expr.op == '+':
            rhs = self.gen_expr_code(expr.a, rvalue=True)
            expr.typ = expr.a.typ
            expr.lvalue = False
            return rhs
        elif expr.op == '-':
            rhs = self.gen_expr_code(expr.a, rvalue=True)
            expr.typ = expr.a.typ
            expr.lvalue = False

            # Implement unary operator with sneaky trick using 0 - v binop:
            zero = self.emit(ir.Const(0, 'zero', rhs.ty))
            return self.emit(ir.Binop(zero, '-', rhs, 'unary_minus', rhs.ty))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))

    def is_bool(self, expr):
        """ Check if an expression is a boolean type """
        if isinstance(expr, ast.Binop) and expr.op in ast.Binop.cond_ops:
            return True
        elif isinstance(expr, ast.Unop) and expr.op in ast.Unop.cond_ops:
            return True
        else:
            return False

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
            ir.Const(1, 'true', self.get_ir_type(expr.typ, expr.loc)))
        self.emit(ir.Jump(final_block))

        # False path:
        self.builder.set_block(false_block)
        false_val = self.emit(
            ir.Const(0, 'false', self.get_ir_type(expr.typ, expr.loc)))
        self.emit(ir.Jump(final_block))

        # Final path:
        self.builder.set_block(final_block)
        phi = self.emit(
            ir.Phi('bool_res', self.get_ir_type(expr.typ, expr.loc)))
        phi.set_incoming(false_block, false_val)
        phi.set_incoming(true_block, true_val)

        # This is for sure no lvalue:
        expr.lvalue = False
        return phi

    def gen_binop(self, expr):
        """ Generate code for binary operation """
        assert isinstance(expr, ast.Binop)
        assert expr.op not in ast.Binop.cond_ops
        expr.lvalue = False

        # Dealing with simple arithmatic
        a_val = self.gen_expr_code(expr.a, rvalue=True)
        b_val = self.gen_expr_code(expr.b, rvalue=True)
        assert isinstance(a_val, ir.Value)
        assert isinstance(b_val, ir.Value)

        # Get best type for result:
        common_type = self.context.get_common_type(expr.a, expr.b)
        expr.typ = common_type

        # TODO: check if operation can be performed on shift and bitwise
        if expr.op not in ['+', '-', '*', '/', '%', '<<', '>>', '|', '&', '^']:
            raise SemanticError("Cannot use {}".format(expr.op))

        # Perform type coercion:
        # TODO: use ir-types, or ast types?
        a_val = self.do_coerce(a_val, expr.a.typ, common_type, expr.loc)
        b_val = self.do_coerce(b_val, expr.b.typ, common_type, expr.loc)

        return self.emit(
            ir.Binop(a_val, expr.op, b_val, "binop", a_val.ty),
            loc=expr.loc)

    def gen_identifier(self, expr):
        """ Generate code for when an identifier was referenced """
        # Generate code for this identifier.
        target = self.context.resolve_symbol(expr)

        # This returns the dereferenced variable.
        if isinstance(target, ast.Variable):
            expr.lvalue = True
            expr.typ = target.typ
            value = self.context.var_map[target]
        elif isinstance(target, ast.Constant):
            expr.lvalue = False
            expr.typ = target.typ
            c_val = self.context.get_constant_value(target)
            c_typ = self.get_ir_type(target.typ, expr.loc)
            value = self.emit(ir.Const(c_val, target.name, c_typ))
        else:
            raise SemanticError(
                'Cannot use {} in expression'.format(target), expr.loc)
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
                expr.typ = target.typ
                value = self.context.var_map[target]
            else:  # pragma: no cover
                raise NotImplementedError(str(target))
            return value

        base = self.gen_expr_code(expr.base)

        # The base is a valid expression:
        assert isinstance(base, ir.Value)
        expr.lvalue = expr.base.lvalue
        basetype = self.context.the_type(expr.base.typ)
        if isinstance(basetype, ast.StructureType):
            self.context.check_type(basetype)
            if basetype.has_field(expr.field):
                expr.typ = basetype.field_type(expr.field)
            else:
                raise SemanticError('{} does not contain field {}'
                                    .format(basetype, expr.field),
                                    expr.loc)
        else:
            raise SemanticError('Cannot select {} of non-structure type {}'
                                .format(expr.field, basetype), expr.loc)

        # expr must be lvalue because we handle with addresses of variables
        assert expr.lvalue

        # Calculate offset into struct:
        base_type = self.context.the_type(expr.base.typ)
        offset = self.emit(
            ir.Const(base_type.field_offset(expr.field), 'offset', ir.ptr))

        # Calculate memory address of field:
        return self.emit(ir.Add(base, offset, "mem_addr", ir.ptr))

    def gen_index_expr(self, expr):
        """ Array indexing """
        base = self.gen_expr_code(expr.base)
        idx = self.gen_expr_code(expr.i, rvalue=True)

        base_typ = self.context.the_type(expr.base.typ)
        if not isinstance(base_typ, ast.ArrayType):
            raise SemanticError('Cannot index non-array type {}'
                                .format(base_typ),
                                expr.base.loc)

        # Make sure the index is an integer:
        idx = self.do_coerce(idx, expr.i.typ, 'int', expr.i.loc)

        # Base address must be a location value:
        assert expr.base.lvalue
        element_type = self.context.the_type(base_typ.element_type)
        element_size = self.context.size_of(element_type)
        expr.typ = base_typ.element_type
        expr.lvalue = True

        int_ir_type = self.get_ir_type('int', expr.loc)

        # Generate constant:
        e_size = self.emit(ir.Const(element_size, 'element_size', int_ir_type))

        # Calculate offset:
        offset = self.emit(
            ir.Mul(idx, e_size, "element_offset", int_ir_type), loc=expr.loc)
        offset = self.emit(
            ir.to_ptr(offset, 'elem_offset'), loc=expr.loc)

        # Calculate address:
        return self.emit(
            ir.Add(base, offset, "element_address", ir.ptr),
            loc=expr.loc)

    def gen_literal_expr(self, expr):
        """ Generate code for literal """
        expr.lvalue = False
        typemap = {int: 'int',
                   float: 'double',
                   bool: 'bool',
                   str: 'string'}
        if type(expr.val) in typemap:
            expr.typ = self.context.get_type(typemap[type(expr.val)])
        else:
            raise SemanticError('Unknown literal type {}'
                                .format(expr.val), expr.loc)
        # Construct correct const value:
        if isinstance(expr.val, str):
            cval = pack_string(expr.val, self.context)
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

        from_type = self.context.the_type(expr.a.typ)
        to_type = self.context.the_type(expr.to_type)
        expr.typ = expr.to_type
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
        else:
            raise SemanticError('Cannot cast {} to {}'
                                .format(from_type, to_type), expr.loc)

    def gen_function_call(self, expr):
        """ Generate code for a function call """
        # Lookup the function in question:
        target_func = self.context.resolve_symbol(expr.proc)
        if not isinstance(target_func, ast.Function):
            raise SemanticError('cannot call {}'.format(target_func), expr.loc)
        ftyp = target_func.typ
        fname = target_func.package.name + '_' + target_func.name

        # Check arguments:
        ptypes = ftyp.parametertypes
        if len(expr.args) != len(ptypes):
            raise SemanticError('{} requires {} arguments, {} given'
                                .format(fname, len(ptypes), len(expr.args)),
                                expr.loc)

        # Evaluate the arguments:
        args = []
        for arg_expr, arg_typ in zip(expr.args, ptypes):
            arg_val = self.gen_expr_code(arg_expr, rvalue=True)
            arg_val = self.do_coerce(
                arg_val, arg_expr.typ, arg_typ, arg_expr.loc)
            args.append(arg_val)

        # determine return type:
        expr.typ = ftyp.returntype

        # Return type will never be an lvalue:
        expr.lvalue = False

        if not self.is_simple_type(ftyp.returntype):
            raise SemanticError(
                'Return value can only be a simple type', expr.loc)

        # Determine return type:
        ret_typ = self.get_ir_type(expr.typ, expr.loc)

        # Emit call:
        return self.emit(
            ir.Call(fname, args, fname + '_rv', ret_typ), loc=expr.loc)
