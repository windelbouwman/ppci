"""
    This module contains the code generation class.
"""

import logging
import struct
from .. import ir
from .. import irutils
from . import astnodes as ast
from .scope import SemanticError


def pack_string(txt):
    """ Pack a string using 4 bytes length followed by text data """
    # TODO: this is probably machine depending?
    length = struct.pack('<I', len(txt))
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
    def __init__(self, diag):
        self.logger = logging.getLogger('c3cgen')
        self.builder = irutils.Builder()
        self.diag = diag
        self.context = None
        self.module_ok = False

    def emit(self, instruction):
        """
            Emits the given instruction to the builder.
            Can be muted for constants.
        """
        self.builder.emit(instruction)
        return instruction

    def gen_globals(self, module, context):
        """ Generate global variables and modules """
        ir_module = ir.Module(module.name)
        context.var_map[module] = ir_module

        # Generate room for global variables:
        for var in module.innerScope.variables:
            ir_var = ir.Variable(var.name, context.size_of(var.typ))
            context.var_map[var] = ir_var
            assert not var.isLocal
            ir_module.add_variable(ir_var)

    def gencode(self, mod, context):
        """ Generate code for a single module """
        assert type(mod) is ast.Module
        self.context = context
        self.builder.prepare()
        self.module_ok = True
        self.logger.info('Generating ir-code for {}'.format(mod.name))
        self.builder.m = self.context.var_map[mod]
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
        return self.builder.m

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
        self.builder.setFunction(ir_function)
        first_block = self.builder.newBlock()
        self.emit(ir.Jump(first_block))
        self.builder.setBlock(first_block)

        # generate room for locals:
        for sym in function.innerScope:
            self.context.check_type(sym.typ)
            var_name = 'var_{}'.format(sym.name)
            variable = ir.Alloc(var_name, self.context.size_of(sym.typ))
            self.emit(variable)
            if sym.isParameter:
                # Parameters can only be simple types (pass by value)
                param_ir_typ = self.get_ir_type(sym.typ, sym.loc)

                # Define parameter for function:
                parameter = ir.Parameter(sym.name, param_ir_typ)
                ir_function.add_parameter(parameter)

                # For paramaters, allocate space and copy the value into
                # memory. Later, the mem2reg pass will extract these values.
                # Move parameter into local copy:
                self.emit(ir.Store(parameter, variable))
            elif isinstance(sym, ast.Variable):
                pass
            else:
                raise NotImplementedError('{}'.format(sym))
            self.context.var_map[sym] = variable

        self.gen_stmt(function.body)
        # self.emit(ir.Move(f.return_value, ir.Const(0)))
        self.emit(ir.Jump(ir_function.epilog))
        self.builder.setFunction(None)

    def get_ir_type(self, cty, loc):
        """ Given a certain type, get the corresponding ir-type """
        cty = self.context.the_type(cty)
        if self.context.equal_types(cty, 'int'):
            return ir.i32
        elif self.context.equal_types(cty, 'double'):
            return ir.f64
        elif self.context.equal_types(cty, 'void'):
            # TODO: how to handle void?
            return ir.i32
        elif self.context.equal_types(cty, 'bool'):
            # Implement booleans as integers:
            return ir.i32
        elif self.context.equal_types(cty, 'byte'):
            return ir.i8
        elif isinstance(cty, ast.PointerType):
            return ir.ptr
        else:
            raise SemanticError(
                'Cannot determine the load type for "{}"'.format(cty), loc)

    def gen_stmt(self, code):
        """ Generate code for a statement """
        try:
            assert isinstance(code, ast.Statement)
            self.builder.setLoc(code.loc)
            if type(code) is ast.Compound:
                for statement in code.statements:
                    self.gen_stmt(statement)
            elif type(code) is ast.Empty:
                pass
            elif type(code) is ast.Assignment:
                self.gen_assignment_stmt(code)
            elif type(code) is ast.ExpressionStatement:
                self.gen_expr_code(code.ex)
                # Check that this is always a void function call
                if not isinstance(code.ex, ast.FunctionCall):
                    raise SemanticError('Not a call expression', code.ex.loc)
                if not self.context.equal_types('void', code.ex.typ):
                    raise SemanticError(
                        'Can only call void functions', code.ex.loc)
            elif type(code) is ast.If:
                self.gen_if_stmt(code)
            elif type(code) is ast.Return:
                self.gen_return_stmt(code)
            elif type(code) is ast.While:
                self.gen_while(code)
            elif type(code) is ast.For:
                self.gen_for_stmt(code)
            else:
                raise NotImplementedError('Unknown stmt {}'.format(code))
        except SemanticError as exc:
            self.error(exc.msg, exc.loc)

    def gen_return_stmt(self, code):
        """ Generate code for return statement """
        ret_val = self.gen_expr_code(code.expr, rvalue=True)
        self.emit(ir.Return(ret_val))
        self.builder.setBlock(self.builder.newBlock())

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
        elif self.context.equal_types('int', typ) and \
                isinstance(wanted_typ, ast.PointerType):
            return self.emit(ir.IntToPtr(ir_val, 'coerce'))
        elif self.context.equal_types('int', typ) and \
                self.context.equal_types('byte', wanted_typ):
            return self.emit(ir.IntToByte(ir_val, 'coerce'))
        elif self.context.equal_types('byte', typ) and \
                self.context.equal_types('int', wanted_typ):
            return self.emit(ir.ByteToInt(ir_val, 'coerce'))
        else:
            raise SemanticError(
                "Cannot use '{}' as '{}'".format(typ, wanted_typ), loc)

    def is_simple_type(self, typ):
        """ Determines if the given type is a simple type """
        typ = self.context.the_type(typ)
        if isinstance(typ, ast.PointerType):
            return True
        elif isinstance(typ, ast.BaseType):
            return True
        return False

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
            lhs_ld = self.emit(ir.Load(lval, 'assign_op_load', load_ty))

            # Now construct the rvalue:
            oper = code.shorthand_operator
            rval = self.emit(ir.Binop(lhs_ld, oper, rval, "binop", rval.ty))

        # TODO: for now treat all stores as volatile..
        # TODO: determine volatile properties from type??
        volatile = True
        return self.emit(ir.Store(rval, lval, volatile=volatile))

    def gen_if_stmt(self, code):
        """ Generate code for if statement """
        true_block = self.builder.newBlock()
        bbfalse = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.gen_cond_code(code.condition, true_block, bbfalse)
        self.builder.setBlock(true_block)
        self.gen_stmt(code.truestatement)
        self.emit(ir.Jump(final_block))
        self.builder.setBlock(bbfalse)
        self.gen_stmt(code.falsestatement)
        self.emit(ir.Jump(final_block))
        self.builder.setBlock(final_block)

    def gen_while(self, code):
        """ Generate code for while statement """
        bbdo = self.builder.newBlock()
        test_block = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(test_block)
        self.gen_cond_code(code.condition, bbdo, final_block)
        self.builder.setBlock(bbdo)
        self.gen_stmt(code.statement)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(final_block)

    def gen_for_stmt(self, code):
        """ Generate for-loop code """
        bbdo = self.builder.newBlock()
        test_block = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.gen_stmt(code.init)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(test_block)
        self.gen_cond_code(code.condition, bbdo, final_block)
        self.builder.setBlock(bbdo)
        self.gen_stmt(code.statement)
        self.gen_stmt(code.final)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(final_block)

    def gen_cond_code(self, expr, bbtrue, bbfalse):
        """ Generate conditional logic.
            Implement sequential logical operators. """
        if type(expr) is ast.Binop:
            if expr.op == 'or':
                # Implement sequential logic:
                second_block = self.builder.newBlock()
                self.gen_cond_code(expr.a, bbtrue, second_block)
                self.builder.setBlock(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op == 'and':
                # Implement sequential logic:
                second_block = self.builder.newBlock()
                self.gen_cond_code(expr.a, second_block, bbfalse)
                self.builder.setBlock(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op in ['==', '>', '<', '!=', '<=', '>=']:
                lhs = self.gen_expr_code(expr.a, rvalue=True)
                rhs = self.gen_expr_code(expr.b, rvalue=True)
                if not self.context.equal_types(expr.a.typ, expr.b.typ):
                    raise SemanticError('Types unequal {} != {}'
                                        .format(expr.a.typ, expr.b.typ),
                                        expr.loc)
                self.emit(ir.CJump(lhs, expr.op, rhs, bbtrue, bbfalse))
            else:
                raise SemanticError('non-bool: {}'.format(expr.op), expr.loc)
            expr.typ = self.context.get_type('bool')
        elif type(expr) is ast.Literal:
            self.gen_expr_code(expr)
            if expr.val:
                self.emit(ir.Jump(bbtrue))
            else:
                self.emit(ir.Jump(bbfalse))
        elif isinstance(expr, ast.Expression):
            # Evaluate expression, make sure it is boolean and compare it
            # with true:
            value = self.gen_expr_code(expr, rvalue=True)
            if not self.context.equal_types(expr.typ, 'bool'):
                self.error('Condition must be boolean', expr.loc)
            true_val = self.emit(ir.Const(1, "true", ir.i32))
            self.emit(ir.CJump(value, '==', true_val, bbtrue, bbfalse))
        else:
            raise NotImplementedError('Unknown cond {}'.format(expr))

        # Check that the condition is a boolean value:
        if not self.context.equal_types(expr.typ, 'bool'):
            self.error('Condition must be boolean', expr.loc)

    def gen_expr_code(self, expr, rvalue=False):
        """ Generate code for an expression. Return the generated ir-value """
        assert isinstance(expr, ast.Expression)
        if type(expr) is ast.Binop:
            value = self.gen_binop(expr)
        elif type(expr) is ast.Unop:
            value = self.gen_unop(expr)
        elif type(expr) is ast.Identifier:
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
                value = self.emit(ir.Const(c_val, target.name, ir.i32))
            elif isinstance(target, ast.Module):
                # TODO: ugly construct here --> do not return a non-ir-value
                return target
            else:
                raise NotImplementedError(str(target))
        elif type(expr) is ast.Deref:
            value = self.gen_dereference(expr)
        elif type(expr) is ast.Member:
            value = self.gen_member_expr(expr)
        elif type(expr) is ast.Index:
            value = self.gen_index_expr(expr)
        elif type(expr) is ast.Literal:
            value = self.gen_literal_expr(expr)
        elif type(expr) is ast.TypeCast:
            value = self.gen_type_cast(expr)
        elif type(expr) is ast.Sizeof:
            # The type of this expression is int:
            expr.lvalue = False  # This is not a location value..
            expr.typ = self.context.get_type('int')
            self.context.check_type(expr.query_typ)
            type_size = self.context.size_of(expr.query_typ)
            value = self.emit(ir.Const(type_size, 'sizeof', ir.i32))
        elif type(expr) is ast.FunctionCall:
            value = self.gen_function_call(expr)
        else:
            raise NotImplementedError('Unknown expr {}'.format(expr))

        # do rvalue trick here, create a r-value when required:
        if rvalue and expr.lvalue:
            # Generate expression code and insert an extra load instruction
            # when required.
            # This means that the value can be used in an expression or as
            # a parameter.

            # Determine loaded type:
            load_ty = self.get_ir_type(expr.typ, expr.loc)

            # Load the value:
            value = self.emit(ir.Load(value, 'loaded', load_ty))

            # This expression is no longer an lvalue
            expr.lvalue = False
        return value

    def gen_dereference(self, expr):
        """ dereference pointer type, which means *(expr) """
        assert type(expr) is ast.Deref
        addr = self.gen_expr_code(expr.ptr)
        ptr_typ = self.context.the_type(expr.ptr.typ)
        expr.lvalue = True
        if type(ptr_typ) is not ast.PointerType:
            raise SemanticError('Cannot deref non-pointer', expr.loc)
        expr.typ = ptr_typ.ptype
        # TODO: why not load the pointed to type?

        # Determine when to introduce an extra load operation.
        # Possibly when the pointed to expression is an lvalue already?
        # TODO: re-cat this mind-melting mess into logical sense
        if expr.ptr.lvalue:
            load_ty = self.get_ir_type(ptr_typ, expr.loc)
            deref_value = self.emit(ir.Load(addr, 'deref', load_ty))
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
        else:
            raise NotImplementedError('Unknown unop {0}'.format(expr.op))

    def gen_binop(self, expr):
        """ Generate code for binary operation """
        assert type(expr) is ast.Binop
        expr.lvalue = False

        # In case of boolean assignment like:
        # 'var bool x = true or false;'
        # Use condition machinery:
        if expr.op in ast.Binop.cond_ops:
            true_block = self.builder.newBlock()
            false_block = self.builder.newBlock()
            final_block = self.builder.newBlock()
            self.gen_cond_code(expr, true_block, false_block)
            # True path:
            self.builder.setBlock(true_block)
            true_val = self.emit(ir.Const(1, 'true', ir.i32))
            self.emit(ir.Jump(final_block))
            # False path:
            self.builder.setBlock(false_block)
            false_val = self.emit(ir.Const(0, 'false', ir.i32))
            self.emit(ir.Jump(final_block))
            # Final path:
            self.builder.setBlock(final_block)
            phi = self.emit(ir.Phi('bool_res', ir.i32))
            phi.set_incoming(false_block, false_val)
            phi.set_incoming(true_block, true_val)
            return phi
        else:
            # Dealing with simple arithmatic
            a_val = self.gen_expr_code(expr.a, rvalue=True)
            b_val = self.gen_expr_code(expr.b, rvalue=True)

            # Get best type for result:
            common_type = self.context.get_common_type(expr.a, expr.b)
            expr.typ = common_type

            # TODO: check if operation can be performed on shift and bitwise
            if expr.op not in ['+', '-', '*', '/', '<<', '>>', '|', '&']:
                raise SemanticError("Cannot use {}".format(expr.op))

            # Perform type coercion:
            # TODO: use ir-types, or ast types?
            a_val = self.do_coerce(a_val, expr.a.typ, common_type, expr.loc)
            b_val = self.do_coerce(b_val, expr.b.typ, common_type, expr.loc)

            return self.emit(
                ir.Binop(a_val, expr.op, b_val, "binop", a_val.ty))

    def gen_member_expr(self, expr):
        """ Generate code for member expression such as struc.mem = 2
            This could also be a module deref!
        """
        base = self.gen_expr_code(expr.base)
        if isinstance(base, ast.Module):
            # Damn, we are referring something inside another module!
            # Invoke scope machinery!
            target = self.context.resolve_symbol(expr)
            if isinstance(target, ast.Variable):
                expr.lvalue = True
                expr.typ = target.typ
                value = self.context.var_map[target]
            elif isinstance(target, ast.Module):
                # TODO: resolve this issue together with above identifier expr
                return target
            else:
                raise NotImplementedError(str(target))
            return value

        # The base is a valid expression:
        expr.lvalue = expr.base.lvalue
        basetype = self.context.the_type(expr.base.typ)
        if type(basetype) is ast.StructureType:
            self.context.check_type(basetype)
            if basetype.hasField(expr.field):
                expr.typ = basetype.fieldType(expr.field)
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
            ir.Const(base_type.fieldOffset(expr.field), 'offset', ir.i32))
        offset = self.emit(ir.IntToPtr(offset, 'offset'))

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

        # Generate constant:
        e_size = self.emit(ir.Const(element_size, 'element_size', ir.i32))

        # Calculate offset:
        offset = self.emit(ir.Mul(idx, e_size, "element_offset", ir.i32))
        offset = self.emit(ir.IntToPtr(offset, 'elem_offset'))

        # Calculate address:
        return self.emit(ir.Add(base, offset, "element_address", ir.ptr))

    def gen_literal_expr(self, expr):
        """ Generate code for literal """
        expr.lvalue = False
        typemap = {int: 'int',
                   float: 'double',
                   bool: 'bool',
                   str: 'string'}
        if type(expr.val) in typemap:
            expr.typ = self.context.scope[typemap[type(expr.val)]]
        else:
            raise SemanticError('Unknown literal type {}'
                                .format(expr.val), expr.loc)
        # Construct correct const value:
        if type(expr.val) is str:
            cval = pack_string(expr.val)
            txt_content = ir.Const(cval, 'strval', ir.i32)
            self.emit(txt_content)
            value = ir.Addr(txt_content, 'addroftxt', ir.i32)
        elif type(expr.val) is int:
            value = ir.Const(expr.val, 'cnst', ir.i32)
        elif type(expr.val) is bool:
            # For booleans, use the integer as storage class:
            val = int(expr.val)
            value = ir.Const(val, 'bool_cnst', ir.i32)
        elif type(expr.val) is float:
            val = float(expr.val)
            value = ir.Const(val, 'bool_cnst', ir.f64)
        else:
            raise NotImplementedError()
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
            return self.emit(ir.IntToPtr(ar, 'int2ptr'))
        elif self.context.equal_types('int', to_type) \
                and isinstance(from_type, ast.PointerType):
            return self.emit(ir.PtrToInt(ar, 'ptr2int'))
        elif type(from_type) is ast.BaseType and from_type.name == 'byte' and \
                type(to_type) is ast.BaseType and to_type.name == 'int':
            return self.emit(ir.ByteToInt(ar, 'byte2int'))
        elif type(from_type) is ast.BaseType and from_type.name == 'int' and \
                type(to_type) is ast.BaseType and to_type.name == 'byte':
            return self.emit(ir.IntToByte(ar, 'bytecast'))
        else:
            raise SemanticError('Cannot cast {} to {}'
                                .format(from_type, to_type), expr.loc)

    def gen_function_call(self, expr):
        """ Generate code for a function call """
        # Lookup the function in question:
        target_func = self.context.resolve_symbol(expr.proc)
        if type(target_func) is not ast.Function:
            raise SemanticError('cannot call {}'.format(target_func))
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
        return self.emit(ir.Call(fname, args, fname + '_rv', ret_typ))
