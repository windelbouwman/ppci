""" Semantics handling for the C programming language.

This class is called whenever the parser has found something. So the interface
between parser and semantics is via a set of function calls.

What this module does:
- Type checking expressions
- Introduction of implicit casting
- Checking initializers for variable declarations

What this logic does not do:
- Evaluating constant values
- Evaluating enum values
- Evaluating sizeof expressions

The result of parser-semantic actions is a type-checked AST.

"""

import difflib
import logging
from .nodes import nodes, types, declarations, statements, expressions
from . import utils, init
from .scope import Scope, RootScope
from .printer import expr_to_str


class CSemantics:
    """ This class handles the C semantics """

    logger = logging.getLogger("semantics")

    def __init__(self, context):
        self.context = context
        self.scope = None
        self._root_scope = RootScope()

        # Define the type for a string:
        self.int_type = self.get_type(["int"])
        self.char_type = self.get_type(["char"])
        self.intptr_type = types.PointerType(self.int_type)

        # Working variables:
        self.compounds = []
        self.switch_stack = []  # switch case levels

    def begin(self):
        """ Enter a new file / compilation unit. """
        self.scope = Scope()

    def finish_compilation_unit(self):
        """ Called at the end of a file / compilation unit. """
        assert self.scope.parent is None  # Must be the topscope now.
        declarations = self.scope.get_declarations()
        compilation_unit = nodes.CompilationUnit(declarations)
        return compilation_unit

    def enter_function(self, function):
        self.logger.debug(
            "Entering function %s %s:%s",
            function.name,
            function.location.filename,
            function.location.row,
        )
        # Nice clean slate:
        assert not self.switch_stack
        self.current_function = function
        self.scope = Scope(self.scope)

        # Define function parameters:
        for argument in function.typ.arguments:
            if argument.name:
                if self.scope.is_defined(argument.name, all_scopes=False):
                    self.error("Illegal redefine", argument.location)
                self.scope.insert(argument)

    def end_function(self, body):
        """ Called at the end of a function """
        # Pop scope and function
        self.scope = self.scope.parent
        function = self.current_function
        self.current_function = None

        if self.scope.is_definition(function.name):
            self.error("invalid redefinition", function.location)
        function.body = body
        assert not self.switch_stack

    def apply_type_modifiers(self, type_modifiers, typ):
        """ Apply the set of type modifiers to the given type """
        # Apply type modifiers in reversed order, starting outwards, going
        # from the outer type to the inside name.
        assert isinstance(typ, types.CType), str(typ)
        for modifier in reversed(type_modifiers):
            if modifier[0] == "POINTER":
                typ = types.PointerType(typ)
                type_qualifiers = modifier[1]
                typ = self.on_type_qualifiers(type_qualifiers, typ)
            elif modifier[0] == "ARRAY":
                size = modifier[1]
                if size and size != "vla":
                    if not self._root_scope.is_const_expr(size):
                        self.error(
                            "Array dimension must be constant", size.location
                        )
                    size = self.coerce(size, self.get_type(["int"]))
                typ = types.ArrayType(typ, size)
            elif modifier[0] == "FUNCTION":
                arguments = modifier[1]
                # print(arguments)
                is_vararg = False
                if arguments and arguments[-1] == "...":
                    # Variadic function!
                    arguments = arguments[:-1]
                    is_vararg = True
                elif len(arguments) == 1 and arguments[0].typ.is_void:
                    # Special case 'int function1(void);'
                    arguments = []

                typ = types.FunctionType(arguments, typ, is_vararg=is_vararg)
            else:  # pragma: no cover
                raise NotImplementedError(str(modifier))
        assert isinstance(typ, types.CType), str(typ)
        return typ

    def on_function_argument(self, typ, name, modifiers, location):
        """ Process a function argument into the proper class """
        typ = self.apply_type_modifiers(modifiers, typ)
        parameter = declarations.ParameterDeclaration(
            None, typ, name, location
        )
        return parameter

    def on_variable_declaration(
        self, storage_class, typ, name, modifiers, location
    ):
        """ Given a declaration, and a declarator, create the proper object """
        typ = self.apply_type_modifiers(modifiers, typ)
        if isinstance(typ, types.FunctionType):
            declaration = self.on_function_declaration(
                storage_class, typ, name, [], location
            )
        else:
            declaration = declarations.VariableDeclaration(
                storage_class, typ, name, None, location
            )

        return declaration

    # Variable initialization!
    def on_variable_initialization(self, variable, expression):
        """ Handle a variable initialized to some value """
        # This is a good point to determine array size and check
        # initial values
        assert isinstance(variable, declarations.VariableDeclaration)

        # Check double initializations
        if self.scope.is_definition(variable.name):
            self.error("Invalid redefinition.", variable.location)

        variable.initial_value = expression

        # Fill array size from elements!
        if (
            isinstance(variable.typ, types.ArrayType)
            and variable.typ.size is None
        ):
            if isinstance(expression, expressions.InitializerList):
                variable.typ.size = len(expression.elements)
            # elif isinstance(expression, expressions.StringLiteral):
            #     variable.typ.size = len(expression.value) + 1
            else:
                pass

    def new_init_cursor(self):
        return init.InitCursor(self.context)

    def on_init_compound_enter(self, init_cursor, typ, location, implicit):
        self.logger.debug("Entering compound at cursor %s", init_cursor)
        if not typ.is_compound:
            self.error("Cannot init non-compound type", location)
        init_cursor.enter_compound(typ, location, implicit)
        return init_cursor

    def init_store(self, init_cursor, value):
        """ Store an initial value at position pointed by cursor. """

        if init_cursor.at_end():
            self.warning("Excess elements!", value.location)

        # Determine if we need implicit init levels:
        target_typ = init_cursor.at_typ()
        while not self._root_scope.equal_types(value.typ, target_typ):
            # If we are at a complex type, implicit descend otherwise cast:
            if target_typ.is_compound:
                init_cursor.enter_compound(target_typ, value.location, True)
                target_typ = init_cursor.at_typ()
            else:
                value = self.coerce(value, target_typ)
                break

        self.logger.debug("Storing %s at cursor %s", value, init_cursor)

        # Retrieve current value to check overwrite:
        previous_value = init_cursor.get_value()
        if previous_value:
            self.warning(
                "This overwrites other initial value.", value.location
            )
            self.warning("previously defined here.", previous_value.location)
        init_cursor.set_value(value)

    def on_array_designator(self, init_cursor, index, location):
        """ Handle array designator. """
        # TODO: Handle things like [4..30] = 23
        # Calculate position:
        pos = self.context.eval_expr(index)

        # Array index must be positive:
        if pos < 0:
            self.error("Array desgnator must be positive", location)

        if not init_cursor.level.typ.is_array:
            self.error(
                "Cannot use array position designators in non-array", location
            )

        # Update current position:
        init_cursor.level.go_to_pos(pos)

    def on_field_designator(self, init_cursor, field_name, location):
        """ Check field designator. """
        init_level = init_cursor.level
        typ = init_level.typ

        if not (typ.is_struct or typ.is_union):
            self.error(
                "Cannot use designator in non-struct/union type", location
            )

        if typ.has_field(field_name):
            field = typ.get_field(field_name)
        else:
            self.error("No such field {}".format(field_name), location)

        # Determine position of field inside the structure:
        init_level.go_to_field(field)

    # Declarations:
    def on_typedef(self, typ, name, modifiers, location):
        """ Handle typedef declaration """
        typ = self.apply_type_modifiers(modifiers, typ)
        declaration = declarations.Typedef(typ, name, location)
        if self.scope.is_defined(name, all_scopes=False):
            sym = self.scope.get(name)
            self.check_redeclaration_type(sym, declaration)
            sym.add_redeclaration(declaration)
        else:
            self.scope.insert(declaration)

    @property
    def in_compound(self):
        return bool(self.compounds)

    def on_function_declaration(
        self, storage_class, typ, name, modifiers, location
    ):
        """ Handle function declaration """
        typ = self.apply_type_modifiers(modifiers, typ)
        declaration = declarations.FunctionDeclaration(
            storage_class, typ, name, location
        )

        return declaration

    # declaration insertion into symbol table.
    def register_declaration(self, declaration):
        """ Register declaration into the scope. """
        # Check if the declared name is already defined:
        if self.scope.is_defined(declaration.name, all_scopes=False):
            # Get the already declared name and figure out what now!
            sym = self.scope.get(declaration.name)
            self.check_redeclaration_type(sym, declaration)

            # re-declarations are only allowed on top level
            if self.in_compound:
                self.invalid_redeclaration(sym, declaration)

            self.check_redeclaration_storage_class(sym, declaration)

            assert not declaration.is_definition()

            # Check initial value?

            # Redefine previous extern is OK!
            sym.add_redeclaration(declaration)
        else:
            # Insert into the current scope:
            self.scope.insert(declaration)

        if self.in_compound:
            statement = statements.DeclarationStatement(
                declaration, declaration.location
            )
            self.add_statement(statement)

    def check_redeclaration_type(self, sym, declaration):
        # The type should match in any case:
        if not self._root_scope.equal_types(sym.typ, declaration.typ):
            self.invalid_redeclaration(sym, declaration)

        if not isinstance(declaration, type(sym.declaration)):
            self.invalid_redeclaration(sym, declaration)

    def check_redeclaration_storage_class(self, sym, declaration):
        """ Test if we specified an invalid combo of storage class. """
        old_storage_class = sym.declaration.storage_class
        new_storage_class = declaration.storage_class
        # None == automatic storage class.
        invalid_combos = [(None, "static"), ("extern", "static")]
        combo = (old_storage_class, new_storage_class)
        if combo in invalid_combos:
            message = "Invalid redefine of storage class. Was {}, but now {}".format(
                old_storage_class, new_storage_class
            )
            self.invalid_redeclaration(sym, declaration, message)

        if not declaration.storage_class:
            if sym.declaration.storage_class:
                declaration.storage_class = sym.declaration.storage_class

    def invalid_redeclaration(
        self, sym, declaration, message="Invalid redefinition"
    ):
        """ Raise an invalid redeclaration error. """
        hint = "First defined here %s" % sym.location
        self.logger.info(hint)
        self.error(message, declaration.location, hints=[hint])

    # Types!
    def on_basic_type(self, type_specifiers, location):
        """ Handle basic type """
        if self._root_scope.is_valid(type_specifiers):
            ctyp = self._root_scope.get_type(type_specifiers)
        else:
            self.error("Invalid type specifiers", location)
        return ctyp

    def on_typename(self, name, location):
        """ Handle the case when a typedef is refered """
        # Lookup typedef
        typedef = self.scope.get(name).declaration
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

        mp = {"struct": types.StructType, "union": types.UnionType}
        klass = mp[kind]

        if tag:
            # Get the tag, or register it
            if self.scope.has_tag(tag):
                ctyp = self.scope.get_tag(tag)
                if not isinstance(ctyp, klass):
                    self.error("Wrong tag kind", location)
            else:
                ctyp = klass()
                self.scope.add_tag(tag, ctyp)
        else:
            ctyp = klass()

        if fields:
            if ctyp.complete:
                self.error("Multiple definitions", location)
            ctyp.fields = fields
        return ctyp

    def on_field_def(
        self, storage_class, ctyp, name, modifiers, bitsize, location
    ):
        """ Handle a struct/union field declaration """
        ctyp = self.apply_type_modifiers(modifiers, ctyp)
        if bitsize is None:
            pass
        else:
            # Bit fields must be of integer type:
            if not ctyp.is_integer:
                self.error("Invalid type for bit-field", location)

        field = types.Field(ctyp, name, bitsize)
        return field

    def on_enum(self, tag, location):
        """ Handle enum declaration """
        if tag:
            if self.scope.has_tag(tag):
                ctyp = self.scope.get_tag(tag)
                if not isinstance(ctyp, types.EnumType):
                    self.error("This tag does not refer to an enum", location)
            else:
                ctyp = types.EnumType()
                self.scope.add_tag(tag, ctyp)
        else:
            ctyp = types.EnumType()
        return ctyp

    def enter_enum_values(self, ctyp, location):
        if ctyp.complete:
            self.error("Enum defined multiple times", location)

    def on_enum_value(self, ctyp, name, value, location):
        """ Handle a single enum value definition """
        if value:
            if not self._root_scope.is_const_expr(value):
                self.error("Enum value must be constant value", value.location)
        declaration = declarations.EnumConstantDeclaration(
            ctyp, name, value, location
        )

        if self.scope.is_defined(name, all_scopes=False):
            sym = self.scope.get(declaration.name)
            self.invalid_redeclaration(sym, declaration)
        else:
            self.scope.insert(declaration)
        return declaration

    def exit_enum_values(self, ctyp, constants, location):
        if len(constants) == 0:
            self.error("Empty enum is not allowed", location)
        ctyp.constants = constants
        # TODO: determine min and max enum values
        # min(enum_values)
        # max(enum_values)
        # TODO: determine storage type!

    @staticmethod
    def on_type_qualifiers(type_qualifiers, ctyp):
        """ Handle type qualifiers """
        if type_qualifiers:
            ctyp.qualifiers = type_qualifiers
        return ctyp

    # Statements!
    @staticmethod
    def on_expression_statement(expression):
        return statements.ExpressionStatement(expression)

    @staticmethod
    def on_label(name, statement, location):
        return statements.Label(name, statement, location)

    def enter_compound_statement(self, location):
        self.scope = Scope(self.scope)
        self.compounds.append([])

    def on_compound_statement(self, location):
        self.scope = self.scope.parent
        inner_statements = self.compounds.pop()
        return statements.Compound(inner_statements, location)

    def add_statement(self, statement):
        """ Helper to emit a statement into the current block. """
        self.compounds[-1].append(statement)

    def on_if(self, condition, then_statement, no, location):
        """ Check if statement """
        condition = self.coerce(condition, self.get_type(["int"]))
        return statements.If(condition, then_statement, no, location)

    def on_switch_enter(self, expression):
        self.switch_stack.append(expression.typ)

    def on_switch_exit(self, expression, statement, location):
        """ Handle switch statement """
        self.switch_stack.pop(-1)
        return statements.Switch(expression, statement, location)

    def on_case(self, value, statement, location):
        """ Handle a case statement """
        if not self.switch_stack:
            self.error("Case statement outside of a switch!", location)

        value = self.coerce(value, self.switch_stack[-1])
        return statements.Case(value, statement, location)

    def on_default(self, statement, location):
        """ Handle a default label """
        if not self.switch_stack:
            self.error("Default statement outside of a switch!", location)

        return statements.Default(statement, location)

    def on_while(self, condition, body, location):
        """ Handle the while statement """
        condition = self.coerce(condition, self.get_type(["int"]))
        return statements.While(condition, body, location)

    def on_do(self, body, condition, location):
        """ The almost extinct dodo! """
        condition = self.coerce(condition, self.get_type(["int"]))
        return statements.DoWhile(body, condition, location)

    def on_for(self, initial, condition, post, body, location):
        """ Check for loop construction """
        if condition:
            condition = self.coerce(condition, self.get_type(["int"]))
        return statements.For(initial, condition, post, body, location)

    def on_return(self, value, location):
        """ Check return statement """
        return_type = self.current_function.typ.return_type
        if value:
            if return_type.is_void:
                self.error(
                    "Cannot return a value from this function", location
                )
            value = self.coerce(value, return_type)
        else:
            if not return_type.is_void:
                self.error("Must return a value from this function", location)
        return statements.Return(value, location)

    # Expressions!
    def on_string(self, value, location):
        """ React on string literal """
        value = value[1:-1]  # Strip of " chars.
        cstr_type = types.ArrayType(self.char_type, len(value) + 1)
        return expressions.StringLiteral(value, cstr_type, location)

    def on_number(self, value, location):
        """ React on numeric literal """
        # Get value from string:
        value, type_specifiers = utils.cnum(value)
        typ = self.get_type(type_specifiers)
        return expressions.NumericLiteral(value, typ, location)

    def on_char(self, value, location):
        """ Process a character literal """
        # Get value from string:
        char_value, kind = utils.charval(value)
        typ = self.get_type(kind)
        return expressions.CharLiteral(char_value, typ, location)

    def on_ternop(self, lhs, op, mid, rhs, location):
        """ Handle ternary operator 'a ? b : c' """
        lhs = self.coerce(lhs, self.int_type)
        # TODO: For now, we use the common type of b and c as the result
        # But is this correct?
        common_type = self.get_common_type(mid.typ, rhs.typ, location)
        mid = self.coerce(mid, common_type)
        rhs = self.coerce(rhs, common_type)
        return expressions.TernaryOperator(
            lhs, op, mid, rhs, common_type, False, location
        )

    def on_binop(self, lhs, op, rhs, location):
        """ Check binary operator """
        if op in ["||", "&&"]:
            result_typ = self.get_type(["int"])
            lhs = self.coerce(lhs, result_typ)
            rhs = self.coerce(rhs, result_typ)
        elif op in [
            "=",
            "+=",
            "-=",
            "*=",
            "%=",
            "/=",
            ">>=",
            "<<=",
            "&=",
            "|=",
            "~=",
            "^=",
        ]:
            # TODO: recurse twice (as '+' and as '=')?
            result_typ = lhs.typ
            if not lhs.lvalue:
                self.error("Expected lvalue", lhs.location)
            rhs = self.coerce(rhs, result_typ)
        elif op == ",":
            result_typ = rhs.typ
        elif op == "+":
            # Handle pointer arithmatic
            if isinstance(lhs.typ, types.IndexableType):
                rhs = self.coerce(rhs, self.int_type)
                result_typ = lhs.typ
            elif isinstance(rhs.typ, types.IndexableType):
                lhs = self.coerce(lhs, self.int_type)
                result_typ = rhs.typ
            else:
                result_typ = self.get_common_type(lhs.typ, rhs.typ, location)
                lhs = self.coerce(lhs, result_typ)
                rhs = self.coerce(rhs, result_typ)
        elif op in ["<", ">", "==", "!=", "<=", ">="]:
            # Booleans are integer type:
            # TODO: assert types are of base arithmatic type
            common_typ = self.get_common_type(lhs.typ, rhs.typ, location)
            lhs = self.coerce(lhs, common_typ)
            rhs = self.coerce(rhs, common_typ)
            result_typ = self.int_type
        else:
            result_typ = self.get_common_type(lhs.typ, rhs.typ, location)
            lhs = self.coerce(lhs, result_typ)
            rhs = self.coerce(rhs, result_typ)

        return expressions.BinaryOperator(
            lhs, op, rhs, result_typ, False, location
        )

    def on_unop(self, op, a, location):
        """ Check unary operator semantics """
        if op in ["x++", "x--", "--x", "++x"]:
            # Increment and decrement in pre and post form
            if not a.lvalue:
                self.error("Expected lvalue", a.location)
            expr = expressions.UnaryOperator(op, a, a.typ, False, location)
        elif op in ["-", "~"]:
            expr = expressions.UnaryOperator(op, a, a.typ, False, location)
        elif op == "+":
            expr = a
        elif op == "*":
            if not isinstance(a.typ, types.IndexableType):
                self.error(
                    "Cannot pointer derefence type {}".format(a.typ),
                    a.location,
                )
            typ = a.typ.element_type
            expr = expressions.UnaryOperator(op, a, typ, True, location)
        elif op == "&":
            if isinstance(a, expressions.VariableAccess) and isinstance(
                a.variable.declaration, declarations.FunctionDeclaration
            ):
                # Function pointer:
                expr = a
            else:
                # L-value access:
                if not a.lvalue:
                    self.error("Expected lvalue", a.location)
                typ = types.PointerType(a.typ)
                expr = expressions.UnaryOperator(op, a, typ, False, location)
        elif op == "!":
            a = self.coerce(a, self.int_type)
            expr = expressions.UnaryOperator(
                op, a, self.int_type, False, location
            )
        else:  # pragma: no cover
            raise NotImplementedError(str(op))
        return expr

    def on_sizeof(self, typ, location):
        """ Handle sizeof contraption """
        expr = expressions.Sizeof(typ, self.int_type, False, location)
        return expr

    def on_cast(self, to_typ, casted_expr, location):
        """ Check explicit casting """
        return expressions.Cast(casted_expr, to_typ, False, location)

    def on_array_index(self, base, index, location):
        """ Check array indexing """
        index = self.coerce(index, self.int_type)

        if not base.lvalue:
            # TODO: must array base be an lvalue?
            self.error("Expected lvalue", location)

        if not isinstance(base.typ, types.IndexableType):
            self.error(
                "Cannot index non array type {}".format(base.typ), location
            )

        typ = base.typ.element_type
        return expressions.ArrayIndex(base, index, typ, True, location)

    def on_field_select(self, base, field_name, location):
        """ Check field select expression """
        if not isinstance(base.typ, types.StructOrUnionType):
            # Maybe we have a pointer to a struct?
            # If so, give a hint about this.
            hints = []
            if isinstance(base.typ, types.PointerType) and isinstance(
                base.typ.element_type, types.StructOrUnionType
            ):
                lhs = expr_to_str(base)
                hints.append(
                    'Did you mean "{0}->{1}" instead of "{0}.{1}"?'.format(
                        lhs, field_name
                    )
                )
            self.error(
                "Selecting a field of non-struct type", location, hints=hints
            )

        if not base.lvalue:
            self.error("Expected lvalue", location)
        # TODO: handle qualifiers?

        if not self.context.has_field(base.typ, field_name):
            valid_field_names = base.typ.get_field_names()
            hint = "This type has those fields: {}".format(valid_field_names)
            self.error(
                "Field {} not part of struct".format(field_name),
                location,
                hints=[hint],
            )

        field = self.context.get_field(base.typ, field_name)
        expr = expressions.FieldSelect(base, field, field.typ, True, location)
        return expr

    def on_builtin_va_start(self, arg_pointer, location):
        """ Check va_start builtin function """
        if not self._root_scope.equal_types(arg_pointer.typ, self.intptr_type):
            self.error("Invalid type for va_start", arg_pointer.location)
        if not arg_pointer.lvalue:
            self.error("Expected lvalue", arg_pointer.location)
        return expressions.BuiltInVaStart(arg_pointer, location)

    def on_builtin_va_arg(self, arg_pointer, typ, location):
        """ Check va_arg builtin function """
        if not self._root_scope.equal_types(arg_pointer.typ, self.intptr_type):
            self.error("Invalid type for va_arg", arg_pointer.location)
        if not arg_pointer.lvalue:
            self.error("Expected lvalue", arg_pointer.location)
        return expressions.BuiltInVaArg(arg_pointer, typ, location)

    def on_builtin_va_copy(self, dest, src, location):
        """ Check va_copy builtin function """
        if not self._root_scope.equal_types(dest.typ, self.intptr_type):
            self.error("Invalid type for va_copy", dest.location)
        if not dest.lvalue:
            self.error("Expected lvalue", dest.location)
        if not self._root_scope.equal_types(src.typ, self.intptr_type):
            self.error("Invalid type for va_copy", src.location)
        return expressions.BuiltInVaCopy(dest, src, location)

    def on_builtin_offsetof(self, typ, member_name, location):
        """ Check offsetof builtin function """
        if not isinstance(typ, types.StructOrUnionType):
            self.error(
                "Can only apply offsetof on structs and unions", location
            )

        # Test if member is a member of the given type now?
        if not self.context.has_field(typ, member_name):
            self.error("Cannot find member {}".format(member_name), location)

        # Test if field is a bitfield:
        field = self.context.get_field(typ, member_name)
        if field.is_bitfield:
            self.error(
                'Attempt to take address of bit-field "{}"'.format(
                    member_name
                ),
                location,
            )

        return expressions.BuiltInOffsetOf(
            typ, member_name, self.int_type, location
        )

    def on_call(self, callee, arguments, location):
        """ Check function call for validity """
        if isinstance(callee.typ, types.FunctionType):
            function_type = callee.typ
        elif isinstance(callee.typ, types.PointerType) and isinstance(
            callee.typ.element_type, types.FunctionType
        ):
            # Function pointer
            function_type = callee.typ.element_type
        else:
            self.error("Calling a non-function", location)

        # Check argument count:
        num_expected = len(function_type.argument_types)
        num_given = len(arguments)
        if function_type.is_vararg:
            if num_given < num_expected:
                self.error(
                    "Expected at least {} arguments, but got {}".format(
                        num_expected, num_given
                    ),
                    location,
                )
        else:
            if num_given != num_expected:
                self.error(
                    "Expected {} arguments, but got {}".format(
                        num_expected, num_given
                    ),
                    location,
                )

        # Check argument types:
        coerced_arguments = []
        for argument, argument_type in zip(
            arguments, function_type.argument_types
        ):
            value = self.coerce(argument, argument_type)
            coerced_arguments.append(value)

        # Append evetual variadic arguments:
        if num_given > num_expected:
            for argument in arguments[num_expected:]:
                coerced_arguments.append(argument)

        # Determine lvalue. If we return a struct, we return an lvalue.
        # otherwise we have an rvalue.
        lvalue = function_type.return_type.is_struct

        expr = expressions.FunctionCall(
            callee,
            coerced_arguments,
            function_type.return_type,
            lvalue,
            location,
        )
        return expr

    def on_variable_access(self, name, location):
        """ Handle variable access """
        if not self.scope.is_defined(name):
            defined_names = self.scope.get_defined_names()
            suggestions = difflib.get_close_matches(name, defined_names)
            hints = []
            for suggestion in suggestions:
                hints.append(
                    '"{}" was not defined, did you mean "{}"?'.format(
                        name, suggestion
                    )
                )
            self.error('Who is this "{}"?'.format(name), location, hints=hints)
        symbol = self.scope.get(name)
        declaration = symbol.declaration
        typ = declaration.typ

        # Determine lvalue and type:
        if isinstance(declaration, declarations.VariableDeclaration):
            lvalue = True
        elif isinstance(declaration, declarations.EnumConstantDeclaration):
            lvalue = False
        elif isinstance(declaration, declarations.ParameterDeclaration):
            lvalue = True
        elif isinstance(declaration, declarations.FunctionDeclaration):
            # Function pointer:
            # expr.typ = types.PointerType(variable.typ)
            lvalue = False
        else:  # pragma: no cover
            self.not_impl("Access to {}".format(variable), location)

        expr = expressions.VariableAccess(symbol, typ, lvalue, location)
        return expr

    # Helpers!
    def coerce(self, expr: expressions.Expression, typ: types.CType):
        """ Try to fit the given expression into the given type """
        assert isinstance(typ, types.CType)
        assert isinstance(expr, expressions.Expression)
        do_cast = False
        from_type = expr.typ
        to_type = typ

        if self._root_scope.equal_types(from_type, to_type):
            pass
        elif isinstance(
            from_type, (types.PointerType, types.EnumType)
        ) and isinstance(to_type, types.BasicType):
            do_cast = True
        elif isinstance(
            from_type, (types.PointerType, types.ArrayType)
        ) and isinstance(to_type, types.PointerType):
            do_cast = True
        elif (
            isinstance(from_type, types.FunctionType)
            and isinstance(to_type, types.PointerType)
            and isinstance(to_type.element_type, types.FunctionType)
            and self._root_scope.equal_types(from_type, to_type.element_type)
        ):
            # Function used as value for pointer to function is fine!
            do_cast = False
        elif isinstance(from_type, types.BasicType) and isinstance(
            to_type, types.IndexableType
        ):
            do_cast = True
        elif isinstance(from_type, types.IndexableType) and isinstance(
            to_type, types.IndexableType
        ):
            # and \
            # self._root_scope.equal_types(
            #    from_type.element_type, to_type.element_type):
            do_cast = True
        elif isinstance(
            from_type, (types.BasicType, types.EnumType)
        ) and isinstance(to_type, (types.BasicType, types.EnumType)):
            # TODO: implement stricter checks
            do_cast = True
        else:
            self.error(
                "Cannot convert {} to {}".format(from_type, to_type),
                expr.location,
            )

        if do_cast:
            expr = expressions.ImplicitCast(expr, typ, False, expr.location)
        return expr

    def get_type(self, type_specifiers):
        """ Retrieve a type by type specifiers """
        return self._root_scope.get_type(type_specifiers)

    def get_common_type(self, typ1, typ2, location):
        """ Given two types, determine the common type.

        The common type is a type they can both be cast to.
        """
        return max([typ1, typ2], key=lambda t: self._get_rank(t, location))

    basic_ranks = {
        types.BasicType.LONGDOUBLE: 110,
        types.BasicType.DOUBLE: 100,
        types.BasicType.FLOAT: 90,
        types.BasicType.ULONGLONG: 71,
        types.BasicType.LONGLONG: 70,
        types.BasicType.ULONG: 61,
        types.BasicType.LONG: 60,
        types.BasicType.UINT: 51,
        types.BasicType.INT: 50,
        types.BasicType.USHORT: 41,
        types.BasicType.SHORT: 40,
        types.BasicType.UCHAR: 31,
        types.BasicType.CHAR: 30,
    }

    def _get_rank(self, typ, location):
        if isinstance(typ, types.BasicType):
            if typ.type_id in self.basic_ranks:
                return self.basic_ranks[typ.type_id]
            else:
                self.error(
                    "Cannot determine type rank for {}".format(typ), location
                )
        elif isinstance(typ, types.EnumType):
            return 80
        elif isinstance(typ, types.PointerType):
            return 83
        elif isinstance(typ, types.ArrayType):
            return 83
        else:
            self.error(
                "Cannot determine type rank for {}".format(typ), location
            )

    def error(self, message, location, hints=None):
        """ Trigger an error at the given location """
        self.context.error(message, location, hints=hints)

    def warning(self, message, location, hints=None):
        """ Trigger a warning at the given location """
        self.context.warning(message, location, hints=hints)

    def not_impl(self, message, location):  # pragma: no cover
        """ Call this function to mark unimplemented code """
        self.error(message, location)
        raise NotImplementedError(message)
