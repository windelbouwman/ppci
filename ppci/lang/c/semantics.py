""" Semantics handling for the C programming language.

This class is called whenever the parser has found something. So the interface
between parser and semantics is via a set of function calls.
"""

import logging
from ...common import CompilerError
from . import nodes, types, declarations, statements, expressions, utils
from .scope import Scope


class CSemantics:
    """ This class handles the C semantics """
    logger = logging.getLogger('semantics')

    def __init__(self, context):
        self.context = context
        self.scope = None

        # Define the type for a string:
        self.int_type = self.get_type(['int'])
        self.cstr_type = types.PointerType(self.get_type(['char']))

    def begin(self):
        self.scope = Scope()
        self.scope.insert(
            declarations.Typedef(self.int_type, '__builtin_va_list', None))
        self.declarations = []

    def finish_compilation_unit(self):
        cu = nodes.CompilationUnit(self.declarations)
        return cu

    def enter_function(self, function):
        self.logger.debug(
            'Entering function %s %s:%s',
            function.name, function.location.filename, function.location.row)
        # Nice clean slate:
        self.current_function = function
        self.scope = Scope(self.scope)

        for argument in function.typ.arguments:
            if argument.name:
                if self.scope.is_defined(argument.name, all_scopes=False):
                    self.error('Illegal redefine', argument.location)
                self.scope.insert(argument)

    def end_function(self, body):
        """ Called at the end of a function """
        self.scope = self.scope.parent
        self.current_function.body = body
        self.current_function = None

    def apply_type_modifiers(self, type_modifiers, typ):
        """ Apply the set of type modifiers to the given type """
        # Apply type modifiers in reversed order, starting outwards, going
        # from the outer type to the inside name.
        assert isinstance(typ, types.CType), str(typ)
        for modifier in reversed(type_modifiers):
            if modifier[0] == 'POINTER':
                typ = types.PointerType(typ)
                type_qualifiers = modifier[1]
                typ = self.on_type_qualifiers(type_qualifiers, typ)
            elif modifier[0] == 'ARRAY':
                size = modifier[1]
                if size:
                    size = self.eval_expr(size)
                typ = types.ArrayType(typ, size)
            elif modifier[0] == 'FUNCTION':
                arguments = modifier[1]
                # print(arguments)
                if arguments and arguments[-1] == '...':
                    arguments = arguments[:-1]
                    is_vararg = True
                else:
                    is_vararg = False
                typ = types.FunctionType(arguments, typ, is_vararg=is_vararg)
            else:  # pragma: no cover
                raise NotImplementedError(str(modifier))
        assert isinstance(typ, types.CType), str(typ)
        return typ

    def on_function_argument(self, typ, name, modifiers, location):
        """ Process a function argument into the proper class """
        typ = self.apply_type_modifiers(modifiers, typ)
        parameter = declarations.ParameterDeclaration(
            None, typ, name, location)
        return parameter

    def on_variable_declaration(
            self, storage_class, typ, name, modifiers, location):
        """ Given a declaration, and a declarator, create the proper object """
        typ = self.apply_type_modifiers(modifiers, typ)
        if isinstance(typ, types.FunctionType):
            declaration = declarations.FunctionDeclaration(
                storage_class, typ, name, location)
        else:
            declaration = declarations.VariableDeclaration(
                storage_class, typ, name, None, location)
        self.add_declaration(declaration)
        return declaration

    def on_variable_initialization(self, variable, expression):
        """ Handle a variable initialized to some value """
        # This is a good point to determine array size and check
        # initial values
        if isinstance(expression, expressions.InitializerList):
            if isinstance(variable.typ, types.ArrayType):
                if variable.typ.size is None:
                    # Determine size from initializer list:
                    variable.typ.size = len(expression.elements)
                else:
                    if variable.typ.size != len(expression.elements):
                        self.error(
                            'Wrong amount of initial values',
                            expression.location)
                for element in expression.elements:
                    print(element)
            elif isinstance(variable.typ, types.StructOrUnionType):
                raise NotImplementedError()
            else:
                raise NotImplementedError()
        else:
            expression = self.coerce(expression, variable.typ)
        variable.initial_value = expression

    def on_typedef(self, typ, name, modifiers, location):
        """ Handle typedef declaration """
        typ = self.apply_type_modifiers(modifiers, typ)
        declaration = declarations.Typedef(typ, name, location)
        self.add_declaration(declaration)
        return declaration

    def on_function_declaration(
            self, storage_class, typ, name, modifiers, location):
        typ = self.apply_type_modifiers(modifiers, typ)
        declaration = declarations.FunctionDeclaration(
            storage_class, typ, name, location)
        # d.arguments = args
        self.add_declaration(declaration)
        return declaration

    def add_global_declaration(self, declaration):
        self.declarations.append(declaration)

    def add_declaration(self, declaration):
        """ Add the given declaration to current scope """

        # print(declaration)
        # Insert into the current scope:
        if self.scope.is_defined(declaration.name, all_scopes=False):
            # The symbol might be a forward declaration:
            sym = self.scope.get(declaration.name)
            if self.context.equal_types(sym.typ, declaration.typ) and \
                    declaration.is_function:
                self.logger.debug(
                    'okay, forward declaration for %s implemented',
                    declaration.name)
            else:
                self.logger.info('First defined here %s', sym.location)
                self.error("Invalid redefinition", declaration.location)
        else:
            self.scope.insert(declaration)

    def get_type(self, type_specifiers):
        """ Retrieve a type by type specifiers """
        assert isinstance(type_specifiers, list)
        return self.context.get_type(type_specifiers)

    def get_common_type(self, typ1, typ2):
        """ Given two types, determine the common type.

        The common type is a type they can both be cast to. """
        # TODO!
        return typ1

    def eval_expr(self, expr):
        """ Evaluate an expression right now! (=at compile time) """
        if isinstance(expr, expressions.Binop):
            lhs = self.eval_expr(expr.a)
            rhs = self.eval_expr(expr.b)
            op = expr.op

            op_map = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x / y,
                '>>': lambda x, y: x >> y,
                '<<': lambda x, y: x << y,
            }
            value = op_map[op](lhs, rhs)
        elif isinstance(expr, expressions.Unop):
            if expr.op in ['-']:
                a = self.eval_expr(expr.a)
                op_map = {
                    '-': lambda x: -x,
                }
                value = op_map[expr.op](a)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))
        elif isinstance(expr, expressions.VariableAccess):
            if isinstance(expr.variable, declarations.ValueDeclaration):
                value = expr.variable.value
            else:
                raise NotImplementedError(str(expr.variable))
        elif isinstance(expr, expressions.NumericLiteral):
            value = expr.value
        elif isinstance(expr, expressions.CharLiteral):
            value = expr.value
        elif isinstance(expr, expressions.Cast):
            # TODO: do some real casting!
            value = self.eval_expr(expr.expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value

    def on_initializer_list(self, values, location):
        return expressions.InitializerList(values, location)

    # Types!
    def on_basic_type(self, type_specifiers, location):
        """ Handle basic type """
        if self.context.is_valid(type_specifiers):
            ctyp = self.context.get_type(type_specifiers)
        else:
            self.error('Invalid type specifiers', location)
        return ctyp

    def on_typename(self, name, location):
        """ Handle the case when a typedef is refered """
        # Lookup typedef
        typedef = self.scope.get(name)
        assert isinstance(typedef, declarations.Typedef)
        ctyp = typedef.typ
        return ctyp  # types.IdentifierType(name, ctyp)

    def on_type(self, typ, modifiers, location):
        """ Called when a type itself is described """
        return self.apply_type_modifiers(modifiers, typ)

    def on_struct_or_union(self, kind, tag, fields, location):
        """ Handle struct or union definition """
        # Layout the struct here!
        assert tag or fields

        mp = {'struct': types.StructType, 'union': types.UnionType}
        klass = mp[kind]

        if tag:
            # Get the tag, or register it
            if self.scope.has_tag(tag):
                ctyp = self.scope.get_tag(tag)
                if not isinstance(ctyp, klass):
                    self.error('Wrong tag kind', location)
            else:
                ctyp = klass()
                self.scope.add_tag(tag, ctyp)
        else:
            ctyp = klass()

        if fields:
            if ctyp.complete:
                self.error('Multiple definitions', location)
            ctyp.fields = self._layout_struct(kind, fields)
        return ctyp

    def _layout_struct(self, kind, fields):
        # Layout the fields in the struct:
        offset = 0
        cfields = []
        for field in fields:
            storage_class, ctyp, name, modifiers, bitsize, location = field
            ctyp = self.apply_type_modifiers(modifiers, ctyp)

            # Calculate bit size:
            if bitsize:
                bitsize = self.eval_expr(bitsize)
            else:
                bitsize = self.context.sizeof(ctyp)
            cfield = types.Field(ctyp, name, offset, bitsize)
            cfields.append(cfield)
            if kind == 'struct':
                offset += bitsize
        return cfields

    def on_enum(self, tag, location):
        if tag:
            if self.scope.has_tag(tag):
                ctyp = self.scope.get_tag(tag)
                if not isinstance(ctyp, types.EnumType):
                    self.error('This tag does not refer to an enum', location)
            else:
                ctyp = types.EnumType()
                self.scope.add_tag(tag, ctyp)
        else:
            ctyp = types.EnumType()
        return ctyp

    def enter_enum_values(self, ctyp, location):
        if ctyp.complete:
            self.error('Enum defined multiple times', location)
        self.current_enum_value = 0
        self.enum_values = []

    def on_enum_value(self, ctyp, name, value, location):
        """ Handle a single enum value definition """
        if value:
            self.current_enum_value = self.eval_expr(value)
        new_value = declarations.ValueDeclaration(
            ctyp, name, self.current_enum_value, location)
        self.add_declaration(new_value)
        self.enum_values.append(new_value)

        # Increase for next enum value:
        self.current_enum_value += 1

    def exit_enum_values(self, ctyp, location):
        if len(self.enum_values) == 0:
            self.error('Empty enum is not allowed', location)
        ctyp.values = self.enum_values
        # TODO: determine min and max enum values
        # min(enum_values)
        # max(enum_values)
        # TODO: determine storage type!

    def _calculate_enum_values(self, ctyp, enum_values):
        for enum_value in enum_values:
            name, value, location = enum_value

    @staticmethod
    def on_type_qualifiers(type_qualifiers, ctyp):
        """ Handle type qualifiers """
        if type_qualifiers:
            ctyp.qualifiers = type_qualifiers
        return ctyp

    # Statements!
    @staticmethod
    def on_declaration_statement(declaration, location):
        return statements.DeclarationStatement(declaration, location)

    @staticmethod
    def on_expression_statement(expression):
        return statements.ExpressionStatement(expression)

    @staticmethod
    def on_label(name, statement, location):
        return statements.Label(name, statement, location)

    @staticmethod
    def on_empty(location):
        return statements.Empty(location)

    def enter_compound_statement(self, location):
        self.scope = Scope(self.scope)

    def on_compound_statement(self, inner_statements, location):
        self.scope = self.scope.parent
        return statements.Compound(inner_statements, location)

    def on_if(self, condition, then_statement, no, location):
        """ Check if statement """
        condition = self.coerce(condition, self.get_type(['int']))
        return statements.If(condition, then_statement, no, location)

    def on_switch(self, expression, statement, location):
        """ Handle switch statement """
        return statements.Switch(expression, statement, location)

    def on_case(self, value, statement, location):
        value = self.eval_expr(value)
        return statements.Case(value, statement, location)

    @staticmethod
    def on_default(statement, location):
        return statements.Default(statement, location)

    @staticmethod
    def on_break(location):
        return statements.Break(location)

    @staticmethod
    def on_continue(location):
        return statements.Continue(location)

    @staticmethod
    def on_goto(label, location):
        return statements.Goto(label, location)

    def on_while(self, condition, body, location):
        condition = self.coerce(condition, self.get_type(['int']))
        return statements.While(condition, body, location)

    def on_do(self, body, condition, location):
        """ The almost extinct dodo! """
        condition = self.coerce(condition, self.get_type(['int']))
        return statements.DoWhile(body, condition, location)

    def on_for(self, initial, condition, post, body, location):
        if condition:
            condition = self.coerce(condition, self.get_type(['int']))
        return statements.For(initial, condition, post, body, location)

    def on_return(self, value, location):
        return_type = self.current_function.typ.return_type
        if value:
            if return_type.is_void:
                self.error(
                    'Cannot return a value from this function', location)
            value = self.coerce(value, return_type)
        else:
            if not return_type.is_void:
                self.error('Must return a value from this function', location)
        return statements.Return(value, location)

    # Expressions!
    def on_string(self, value, location):
        """ React on string literal """
        expr = expressions.StringLiteral(value, location)
        expr.typ = self.cstr_type
        expr.lvalue = False
        return expr

    def on_number(self, value, location):
        """ React on numeric literal """
        # Get value from string:
        v = utils.cnum(value)
        # TODO: this does not have to be int!
        assert isinstance(v, int)

        expr = expressions.NumericLiteral(v, location)
        # TODO: handle other types such as long long
        expr.typ = self.get_type(['int'])
        expr.lvalue = False
        return expr

    def on_char(self, value, location):
        """ Process a character literal """
        # Get value from string:
        char_value, kind = utils.charval(value)
        expr = expressions.CharLiteral(char_value, location)
        expr.typ = self.get_type(kind)
        expr.lvalue = False
        return expr

    def on_ternop(self, lhs, op, mid, rhs, location):
        """ Handle ternary operator 'a ? b : c' """
        lhs = self.coerce(lhs, self.int_type)
        # TODO: For now, we use the common type of b and c as the result
        # But is this correct?
        common_type = self.get_common_type(mid.typ, rhs.typ)
        mid = self.coerce(mid, common_type)
        rhs = self.coerce(rhs, common_type)
        expr = expressions.Ternop(lhs, op, mid, rhs, location)
        expr.typ = common_type
        expr.lvalue = False
        return expr

    def on_binop(self, lhs, op, rhs, location):
        """ Check binary operator """
        if op in ['||', '&&']:
            common_typ = self.get_type(['int'])
        elif op in [
                '=', '+=', '-=', '*=', '%=', '/=',
                '>>=', '<<=',
                '&=', '|=', '~=', '^=']:
            common_typ = lhs.typ
            if not lhs.lvalue:
                self.error('Expected lvalue', lhs.location)
        else:
            common_typ = self.get_common_type(lhs.typ, rhs.typ)

        # Coerce always, except when comma operator is used:
        if op == ',':
            common_typ = rhs.typ
        else:
            lhs = self.coerce(lhs, common_typ)
            rhs = self.coerce(rhs, common_typ)

        expr = expressions.Binop(lhs, op, rhs, location)
        if op in ['<', '>', '==', '!=', '<=', '>=', '||', '&&']:
            # Booleans are integer type:
            expr.typ = self.get_type(['int'])
        else:
            expr.typ = common_typ
        expr.lvalue = False
        return expr

    def on_unop(self, op, a, location):
        """ Check unary operator semantics """
        if op in ['x++', 'x--', '--x', '++x']:
            # Increment and decrement in pre and post form
            if not a.lvalue:
                self.error('Expected lvalue', a.location)
            expr = expressions.Unop(op, a, location)
            expr.typ = expr.a.typ
            expr.lvalue = False
        elif op in ['-', '~']:
            expr = expressions.Unop(op, a, location)
            expr.typ = expr.a.typ
            expr.lvalue = False
        elif op == '*':
            if not isinstance(a.typ, types.IndexableType):
                self.error(
                    'Cannot pointer derefence type {}'.format(a.typ),
                    a.location)
            expr = expressions.Unop(op, a, location)
            expr.typ = expr.a.typ.element_type
            expr.lvalue = True
        elif op == '&':
            if not a.lvalue:
                self.error('Expected lvalue', a.location)
            expr = expressions.Unop(op, a, location)
            expr.typ = types.PointerType(expr.a.typ)
            expr.lvalue = False
        elif op == '!':
            a = self.coerce(a, self.get_type(['int']))
            expr = expressions.Unop(op, a, location)
            expr.typ = self.get_type(['int'])
            expr.lvalue = False
        else:  # pragma: no cover
            raise NotImplementedError(str(op))
        return expr

    def on_sizeof(self, typ, loc):
        expr = expressions.Sizeof(typ, loc)
        expr.typ = self.get_type(['int'])
        expr.lvalue = False
        return expr

    def on_cast(self, to_typ, casted_expr, loc):
        """ Check explicit casting """
        expr = expressions.Cast(to_typ, casted_expr, loc)
        expr.typ = expr.to_typ
        expr.lvalue = False  # or expr.expr.lvalue?
        return expr

    def on_array_index(self, base, index, location):
        """ Check array indexing """
        int_type = self.get_type(['int'])
        index = self.coerce(index, int_type)
        if not base.lvalue:
            # TODO: must array base be an lvalue?
            self.error('Expected lvalue', base)
        if not isinstance(base.typ, types.IndexableType):
            self.error(
                'Cannot index non array type {}'.format(
                    base.typ), location)

        expr = expressions.ArrayIndex(base, index, location)
        expr.typ = base.typ.element_type
        expr.lvalue = True
        return expr

    def on_field_select(self, base, field, location):
        """ Check field select expression """
        if not base.lvalue:
            self.error('Expected lvalue', location)
        # TODO: handle qualifiers?

        if not isinstance(base.typ, types.StructOrUnionType):
            self.error('Selecting a field of non-struct type', location)

        if not base.typ.has_field(field):
            self.error('Field {} not part of struct'.format(field), location)

        field = base.typ.get_field(field)
        expr = expressions.FieldSelect(base, field, location)
        expr.typ = field.typ
        expr.lvalue = True
        return expr

    def on_call(self, name, arguments, location):
        """ Check function call for validity """
        # Lookup the function:
        if not self.scope.is_defined(name):
            self.error('Who is this?', location)
        function = self.scope.get(name)

        # Check for funky-ness:
        if not isinstance(function, declarations.FunctionDeclaration):
            self.error('Calling a non-function', location)

        # Check argument count:
        num_expected = len(function.typ.argument_types)
        num_given = len(arguments)
        if num_given != num_expected:
            self.error('Expected {} arguments, but got {}'.format(
                num_expected, num_given), location)

        # Check argument types:
        coerced_arguments = []
        for argument, argument_type in zip(
                arguments, function.typ.argument_types):
            value = self.coerce(argument, argument_type)
            coerced_arguments.append(value)
        expr = expressions.FunctionCall(function, coerced_arguments, location)
        expr.lvalue = False
        expr.typ = function.typ.return_type
        return expr

    def on_variable_access(self, name, location):
        """ Handle variable access """
        if not self.scope.is_defined(name):
            self.error('Who is this?', location)
        variable = self.scope.get(name)
        expr = expressions.VariableAccess(variable, location)
        expr.typ = variable.typ
        if isinstance(variable, declarations.VariableDeclaration):
            expr.lvalue = True
        elif isinstance(variable, declarations.ValueDeclaration):
            expr.lvalue = False
        elif isinstance(variable, declarations.ParameterDeclaration):
            expr.lvalue = True
        elif isinstance(variable, declarations.FunctionDeclaration):
            # Function pointer?
            expr.lvalue = True
        else:  # pragma: no cover
            self.not_impl('Access to {}'.format(variable), location)
        return expr

    # Helpers!
    def coerce(self, expr: expressions.Expression, typ: types.CType):
        """ Try to fit the given expression into the given type """
        do_cast = False
        from_type = expr.typ
        to_type = typ

        if self.context.equal_types(from_type, to_type):
            pass
        elif isinstance(from_type, (types.PointerType, types.EnumType)) and \
                isinstance(to_type, types.BareType):
            do_cast = True
        elif isinstance(
                from_type,
                (types.PointerType, types.ArrayType, types.FunctionType)) and \
                isinstance(to_type, types.PointerType):
            do_cast = True
        elif isinstance(from_type, types.BareType) and \
                isinstance(to_type, types.PointerType):
            do_cast = True
        elif isinstance(from_type, types.BareType) and \
                isinstance(to_type, (types.BareType, types.EnumType)):
            # TODO: implement stricter checks
            do_cast = True
        else:
            self.error(
                'Cannot convert {} to {}'.format(from_type, to_type),
                expr.location)

        if do_cast:
            # TODO: is it true that the source must an lvalue?
            # assert not expr.lvalue
            expr = expressions.ImplicitCast(typ, expr, expr.location)
            expr.typ = typ
            expr.lvalue = False
        return expr

    def error(self, message, location):
        """ Trigger an error at the given location """
        raise CompilerError(message, loc=location)

    def not_impl(self, message, location):
        self.error(message, location)
        raise NotImplementedError(message)
