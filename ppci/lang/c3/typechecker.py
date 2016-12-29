import logging
from . import astnodes as ast
from .scope import SemanticError


class TypeChecker:
    """ Type checker """
    logger = logging.getLogger('c3check')

    def __init__(self, diag, context):
        self.diag = diag
        self.context = context

    def check(self):
        """ Check everything """
        for module in self.context.modules:
            self.check_module(module)

    def check_module(self, module: ast.Module):
        """ Check a module """
        assert isinstance(module, ast.Module)
        self.module_ok = True
        self.logger.info('Checking module %s', module.name)
        try:
            # Check defined types of this module:
            for typ in module.types:
                self.check_type(typ)

            for con in module.constants:
                self.check_type(con.typ)
                self.check_expr(con.value)
                con.value = self.do_coerce(con.value, con.typ)

            # Check global variables:
            for var in module.variables:
                assert not var.isLocal
                self.check_variable(var)
        except SemanticError as ex:
            self.error(ex.msg, ex.loc)

        # Check functions:
        for func in module.functions:
            # Try per function, in case of error, continue with next
            try:
                self.check_function(func)
            except SemanticError as ex:
                self.error(ex.msg, ex.loc)

        if not self.module_ok:
            raise SemanticError("Errors occurred", None)

    def check_type(self, typ, first=True, byname=False):
        """ Check a type.

        Determine struct offsets and check for recursiveness by using
        mark and sweep algorithm.

        The calling function could call this function with first set
        to clear the marks.
        """

        # Reset the mark and sweep:
        if first:
            self.got_types = set()

        # Resolve the type:
        typ = self.context.get_type(typ, not byname)

        # Check for recursion:
        if typ in self.got_types:
            raise SemanticError('Recursive data type {}'.format(typ), None)

        if isinstance(typ, ast.BaseType):
            pass
        elif isinstance(typ, ast.PointerType):
            # If a pointed type is detected, stop structural
            # equivalence. This to allow linked lists!
            self.check_type(typ.ptype, first=False, byname=True)
        elif isinstance(typ, ast.StructureType):
            self.got_types.add(typ)
            # Setup offsets of fields. Is this the right place?:
            # TODO: move this struct offset calculation.
            offset = 0
            for struct_member in typ.fields:
                self.check_type(struct_member.typ, first=False)
                struct_member.offset = offset
                offset = offset + self.context.size_of(struct_member.typ)
        elif isinstance(typ, ast.ArrayType):
            self.check_type(typ.element_type, first=False)
        elif isinstance(typ, ast.DefinedType):
            pass
        else:  # pragma: no cover
            raise NotImplementedError('{} not implemented'.format(type(typ)))

    def check_variable(self, var):
        """ Check a variable and especially its initial value """
        self.check_type(var.typ)
        if var.ival:
            var.ival = self.check_initial_value(var.ival, var.typ)

    def check_initial_value(self, ival, typ):
        """ Ensure that the initial value fits the given type """
        typ = self.context.get_type(typ)
        if isinstance(typ, ast.ArrayType):
            if not isinstance(ival, ast.ExpressionList):
                raise SemanticError('Invalid array initialization', ival.loc)

            # TODO: can we do legit constant evaluation here?
            size = self.context.eval_const(typ.size)
            if len(ival.expressions) != size:
                raise SemanticError(
                    '{} initial values given, expected {}'.format(
                        len(ival.expressions), size),
                    ival.loc)
            new_expressions = []
            for expr in ival.expressions:
                new_expr = self.check_initial_value(expr, typ.element_type)
                new_expressions.append(new_expr)
            ival.expressions = new_expressions
            return ival
        elif isinstance(typ, ast.StructureType):
            print(ival)
            if not isinstance(ival, ast.NamedExpressionList):
                raise SemanticError('Invalid struct initialization', ival.loc)
            if len(ival.expressions) != len(typ.fields):
                raise SemanticError('Wrong number of given fields', ival.loc)
            new_expressions = []
            for ival2, fld in zip(ival.expressions, typ.fields):
                field, expr = ival2
                if field != fld.name:
                    raise SemanticError('Wrong name of struct field', expr.loc)
                new_expr = self.check_initial_value(expr, fld.typ)
                new_expressions.append((field, new_expr))
            ival.expressions = new_expressions
            return ival
        else:
            self.check_expr(ival)
            return self.do_coerce(ival, typ)

    def check_function(self, function):
        """ Check a function. """
        for param in function.parameters:
            self.check_type(param.typ)

            # Parameters can only be simple types (pass by value)
            if not self.context.is_simple_type(param.typ):
                raise SemanticError(
                    'Function parameters can only be simple types',
                    function.loc)

        if not self.context.is_simple_type(function.typ.returntype):
            raise SemanticError(
                'Functions can only return simple types', function.loc)

        for sym in function.inner_scope:
            self.check_type(sym.typ)

        self.current_function = function
        if function.body:
            self.check_stmt(function.body)
        self.current_function = None

    def check_stmt(self, code: ast.Statement):
        """ Check a statement """
        try:
            assert isinstance(code, ast.Statement)
            if isinstance(code, ast.Compound):
                for statement in code.statements:
                    self.check_stmt(statement)
            elif isinstance(code, ast.Empty):
                pass
            elif isinstance(code, ast.Assignment):
                self.check_assignment_stmt(code)
            elif isinstance(code, ast.VariableDeclaration):
                self.check_variable(code.var)
            elif isinstance(code, ast.ExpressionStatement):
                # Check that this is always a void function call
                if not isinstance(code.ex, ast.FunctionCall):
                    raise SemanticError('Not a call expression', code.ex.loc)
                value = self.check_function_call(code.ex)
                if not self.context.equal_types('void', code.ex.typ):
                    raise SemanticError(
                        'Can only call void functions', code.ex.loc)
                assert value is None
            elif isinstance(code, ast.If):
                self.check_if_stmt(code)
            elif isinstance(code, ast.Return):
                self.check_return_stmt(code)
            elif isinstance(code, ast.While):
                self.check_while(code)
            elif isinstance(code, ast.For):
                self.check_for_stmt(code)
            elif isinstance(code, ast.Switch):
                self.check_switch_stmt(code)
            else:  # pragma: no cover
                raise NotImplementedError(str(code))
        except SemanticError as exc:
            self.error(exc.msg, exc.loc)

    def check_if_stmt(self, code):
        """ Check if statement """
        self.check_condition(code.condition)
        self.check_stmt(code.truestatement)
        self.check_stmt(code.falsestatement)

    def check_while(self, code):
        """ Check while statement """
        self.check_condition(code.condition)
        self.check_stmt(code.statement)

    def check_for_stmt(self, code):
        """ Check a for-loop """
        self.check_stmt(code.init)
        self.check_condition(code.condition)
        self.check_stmt(code.statement)
        self.check_stmt(code.final)

    def check_switch_stmt(self, switch):
        """ Check a switch statement """
        self.check_expr(switch.expression, rvalue=True)
        if not self.context.equal_types('int', switch.expression.typ):
            raise SemanticError(
                'Switch condition must be integer', switch.expression.loc)

        default_block = False
        for option_val, option_code in switch.options:
            self.check_stmt(option_code)

            if option_val is None:
                # default case
                default_block = True
            else:
                self.check_expr(option_val)

        if not default_block:
            raise SemanticError(
                'No default case specified in switch-case', switch.loc)

    def check_return_stmt(self, code):
        """ Check a return statement """
        if code.expr:
            if self.context.equal_types(
                    'void', self.current_function.typ.returntype):
                raise SemanticError(
                    'Cannot return value from void function', code.expr.loc)
            self.check_expr(code.expr, rvalue=True)
            code.expr = self.do_coerce(
                code.expr, self.current_function.typ.returntype)
        else:
            if not self.context.equal_types(
                    'void', self.current_function.typ.returntype):
                raise SemanticError('Cannot return nothing', code.loc)

    def check_assignment_stmt(self, code):
        """ Check code for assignment statement """
        # Evaluate left hand side:
        self.check_expr(code.lval)

        # Check that the left hand side is a simple type:
        if not self.context.is_simple_type(code.lval.typ):
            raise SemanticError(
                'Cannot assign to complex type {}'.format(code.lval.typ),
                code.loc)

        # Check that left hand is an lvalue:
        if not code.lval.lvalue:
            raise SemanticError(
                'No valid lvalue {}'.format(code.lval), code.lval.loc)

        # Evaluate right hand side (and make it rightly typed):
        self.check_expr(code.rval, rvalue=True)
        code.rval = self.do_coerce(code.rval, code.lval.typ)

    def check_condition(self, expr):
        """ Check condition expression """
        if isinstance(expr, ast.Binop):
            if expr.op in ['and', 'or']:
                self.check_condition(expr.a)
                self.check_condition(expr.b)
            elif expr.op in ['==', '>', '<', '!=', '<=', '>=']:
                self.check_expr(expr.a, rvalue=True)
                self.check_expr(expr.b, rvalue=True)
                common_type = self.context.get_common_type(
                    expr.a, expr.b, expr.loc)
                expr.a = self.do_coerce(expr.a, common_type)
                expr.b = self.do_coerce(expr.b, common_type)
            else:
                raise SemanticError('non-bool: {}'.format(expr.op), expr.loc)
            expr.typ = self.context.get_type('bool')
        elif isinstance(expr, ast.Literal):
            self.check_expr(expr)
        elif isinstance(expr, ast.Unop) and expr.op == 'not':
            self.check_condition(expr.a)
            expr.typ = self.context.get_type('bool')
        elif isinstance(expr, ast.Expression):
            # Evaluate expression, make sure it is boolean and compare it
            # with true:
            self.check_expr(expr, rvalue=True)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check that the condition is a boolean value:
        if not self.context.equal_types(expr.typ, 'bool'):
            self.error('Condition must be boolean', expr.loc)

    def check_expr(self, expr: ast.Expression, rvalue=False):
        """ Check an expression. """
        assert isinstance(expr, ast.Expression)
        if expr.is_bool:
            self.check_bool_expr(expr)
        else:
            if isinstance(expr, ast.Binop):
                self.check_binop(expr)
            elif isinstance(expr, ast.Unop):
                self.check_unop(expr)
            elif isinstance(expr, ast.Identifier):
                self.check_identifier(expr)
            elif isinstance(expr, ast.Deref):
                self.check_dereference(expr)
            elif isinstance(expr, ast.Member):
                self.check_member_expr(expr)
            elif isinstance(expr, ast.Index):
                self.check_index_expr(expr)
            elif isinstance(expr, ast.Literal):
                self.check_literal_expr(expr)
            elif isinstance(expr, ast.TypeCast):
                self.check_type_cast(expr)
            elif isinstance(expr, ast.Sizeof):
                self.check_sizeof(expr)
            elif isinstance(expr, ast.FunctionCall):
                self.check_function_call(expr)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))

        # do rvalue trick here, create a r-value when required:
        if rvalue and expr.lvalue:
            # Generate expression code and insert an extra load instruction
            # when required.
            # This means that the value can be used in an expression or as
            # a parameter.

            # Type must be simple, or a pointer at this point!
            val_typ = self.context.get_type(expr.typ)
            assert isinstance(val_typ, (ast.PointerType, ast.BaseType))

            # This expression is no longer an lvalue
            expr.lvalue = False

    def check_bool_expr(self, expr):
        """ Check boolean expression """
        self.check_condition(expr)

        # This is for sure no lvalue:
        expr.lvalue = False

    def check_sizeof(self, expr):
        # This is not a location value..
        expr.lvalue = False

        # The type of this expression is int:
        expr.typ = self.context.get_type('int')

        self.check_type(expr.query_typ)

    def check_dereference(self, expr: ast.Deref):
        """ dereference pointer type, which means *(expr) """
        assert isinstance(expr, ast.Deref)

        # Make sure to have the rvalue of the pointer:
        self.check_expr(expr.ptr, rvalue=True)

        # A pointer is always a lvalue:
        expr.lvalue = True

        ptr_typ = self.context.get_type(expr.ptr.typ)
        if not isinstance(ptr_typ, ast.PointerType):
            raise SemanticError('Cannot deref {}'.format(ptr_typ), expr.loc)
        expr.typ = ptr_typ.ptype

    def check_unop(self, expr):
        """ Check unary operator """
        if expr.op == '&':
            self.check_expr(expr.a)
            if not expr.a.lvalue:
                raise SemanticError('No valid lvalue', expr.a.loc)
            expr.typ = ast.PointerType(expr.a.typ)
            expr.lvalue = False
        elif expr.op in ['+', '-']:
            self.check_expr(expr.a, rvalue=True)
            expr.typ = expr.a.typ
            expr.lvalue = False
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))

    def check_binop(self, expr: ast.Binop):
        """ Check binary operation """
        assert isinstance(expr, ast.Binop)
        assert expr.op not in ast.Binop.cond_ops
        expr.lvalue = False

        # Dealing with simple arithmatic
        self.check_expr(expr.a, rvalue=True)
        self.check_expr(expr.b, rvalue=True)

        # Get best type for result:
        common_type = self.context.get_common_type(expr.a, expr.b, expr.loc)
        expr.typ = common_type

        # TODO: check if operation can be performed on shift and bitwise
        # if expr.op not in [
        #       '+', '-', '*', '/', '%', '<<', '>>', '|', '&', '^']:
        #     raise SemanticError("Cannot use {}".format(expr.op))

        # Perform type coercion:
        expr.a = self.do_coerce(expr.a, common_type)
        expr.b = self.do_coerce(expr.b, common_type)

    def check_identifier(self, expr):
        """ Check identifier usage """
        # Generate code for this identifier.
        target = self.context.resolve_symbol(expr)

        # This returns the dereferenced variable.
        if isinstance(target, ast.Variable):
            expr.lvalue = True
            expr.typ = target.typ
        elif isinstance(target, ast.Constant):
            expr.lvalue = False
            expr.typ = target.typ
        else:
            raise SemanticError(
                'Cannot use {} in expression'.format(target), expr.loc)

    def check_member_expr(self, expr):
        """ Check expressions such as struc.mem """
        if self.is_module_ref(expr):
            # Damn, we are referring something inside another module!
            # Invoke scope machinery!
            target = self.context.resolve_symbol(expr)
            if isinstance(target, ast.Variable):
                expr.lvalue = True
                expr.typ = target.typ
            else:  # pragma: no cover
                raise NotImplementedError(str(target))
            return

        self.check_expr(expr.base)

        # The base is a valid expression:
        expr.lvalue = expr.base.lvalue
        basetype = self.context.get_type(expr.base.typ)
        if isinstance(basetype, ast.StructureType):
            self.check_type(basetype)
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

    def is_module_ref(self, expr):
        """ Determine whether a module is referenced """
        if isinstance(expr, ast.Member):
            if isinstance(expr.base, ast.Identifier):
                target = self.context.resolve_symbol(expr.base)
                return isinstance(target, ast.Module)
            elif isinstance(expr, ast.Member):
                return self.is_module_ref(expr.base)
        return False

    def check_index_expr(self, expr):
        """ Array indexing """
        self.check_expr(expr.base)
        self.check_expr(expr.i, rvalue=True)

        base_typ = self.context.get_type(expr.base.typ)
        if not isinstance(base_typ, ast.ArrayType):
            raise SemanticError('Cannot index non-array type {}'
                                .format(base_typ),
                                expr.base.loc)

        # Make sure the index is an integer:
        expr.i = self.do_coerce(expr.i, 'int')

        # Base address must be a location value:
        assert expr.base.lvalue
        expr.typ = base_typ.element_type
        expr.lvalue = True

    def check_literal_expr(self, expr):
        """ Check literal """
        expr.lvalue = False
        typemap = {int: 'int',
                   float: 'double',
                   bool: 'bool',
                   str: 'string'}
        expr.typ = self.context.get_type(typemap[type(expr.val)])

    def check_type_cast(self, expr):
        """ Check type cast """
        # When type casting, the rvalue property is lost.
        self.check_expr(expr.a, rvalue=True)
        expr.lvalue = False

        expr.typ = expr.to_type

    def check_function_call(self, expr):
        """ Check function call """
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
        new_args = []
        for arg_expr, arg_typ in zip(expr.args, ptypes):
            self.check_expr(arg_expr, rvalue=True)
            arg_expr = self.do_coerce(arg_expr, arg_typ)
            new_args.append(arg_expr)
        expr.args = new_args

        # determine return type:
        expr.typ = ftyp.returntype

        # Return type will never be an lvalue:
        expr.lvalue = False

        if not self.context.is_simple_type(ftyp.returntype):
            raise SemanticError(
                'Return value can only be a simple type', expr.loc)

    def do_coerce(self, expr, typ):
        """ Try to convert expression into the given type.

        expr: the expression value with a certain type
        typ: the type that it must be
        Raises an error is the conversion cannot be done.
        """
        from_type = self.context.get_type(expr.typ)
        to_type = self.context.get_type(typ)

        # Evaluate types from pointer, unsigned, signed to floating point:
        if self.context.equal_types(from_type, to_type):
            # no cast required
            auto_cast = False
        elif isinstance(from_type, ast.PointerType) and \
                isinstance(to_type, ast.PointerType):
            # Pointers are pointers, no matter the pointed data.
            # But a conversion of type is still needed:
            auto_cast = True
        elif isinstance(from_type, ast.UnsignedIntegerType) and \
                isinstance(to_type, ast.PointerType):
            # Unsigned integers can be used as pointers without problem
            # Signed integers form a problem, because those can be negative
            # and thus must be casted explicitly.
            auto_cast = True
        elif isinstance(from_type, ast.UnsignedIntegerType) and \
                isinstance(to_type, ast.UnsignedIntegerType) and \
                from_type.bits <= to_type.bits:
            auto_cast = True
        elif isinstance(from_type, ast.SignedIntegerType) and \
                isinstance(to_type, ast.SignedIntegerType) and \
                from_type.bits <= to_type.bits:
            auto_cast = True
        elif isinstance(from_type, ast.UnsignedIntegerType) and \
                isinstance(to_type, ast.SignedIntegerType) and \
                from_type.bits < to_type.bits - 1:
            auto_cast = True
        elif isinstance(from_type, ast.UnsignedIntegerType) and \
                isinstance(to_type, ast.FloatType) and \
                from_type.bits < to_type.fraction_bits:
            auto_cast = True
        elif isinstance(from_type, ast.SignedIntegerType) and \
                isinstance(to_type, ast.FloatType) and \
                from_type.bits < to_type.fraction_bits:
            auto_cast = True
        elif isinstance(from_type, ast.FloatType) and \
                isinstance(to_type, ast.FloatType) and \
                from_type.bits < to_type.bits:
            auto_cast = True
        elif isinstance(from_type, ast.SignedIntegerType) and \
                isinstance(to_type, (ast.UnsignedIntegerType, ast.FloatType)):
            # For now, allow auto-cast, until better way of
            # casting constant integer to byte type is found:
            # TODO: remove this branch!
            auto_cast = True
        elif isinstance(from_type, ast.FloatType) and \
                isinstance(to_type, ast.FloatType):
            # TODO: remove this hack!
            auto_cast = True
        elif isinstance(from_type, ast.IntegerType) and \
                isinstance(to_type, ast.PointerType):
            # TODO: remove this hack!
            auto_cast = True
        else:
            raise SemanticError(
                "Cannot use '{}' as '{}'".format(from_type, to_type), expr.loc)
        if auto_cast:
            expr = ast.TypeCast(typ, expr, expr.loc)
        self.check_expr(expr)
        return expr

    def error(self, msg, loc=None):
        """ Emit error to diagnostic system and mark package as invalid """
        self.module_ok = False
        self.logger.error(msg)
        self.diag.error(msg, loc)
