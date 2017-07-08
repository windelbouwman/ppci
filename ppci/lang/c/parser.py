""" C parsing logic.

The C parsing is implemented in a recursive descent parser.

The following parts can be distinguished:
- Declaration parsing: parsing types and declarations
- Statement parsing: dealing with the C statements, like for, if, etc..
- Expression parsing: parsing the C expressions.
"""

import logging
from ..tools.recursivedescent import RecursiveDescentParser
from . import nodes


class CParser(RecursiveDescentParser):
    """ C Parser.

    Implemented in a recursive descent way, like the CLANG[1]
    frontend for llvm, also without the lexer hack[2]. See for the gcc
    c parser code [3]. Also interesting is the libfim cparser frontend [4].

    The clang parser is very versatile, it can handle C, C++, objective C
    and also do code completion. This one is very simple, it can only
    parse C.

    [1] http://clang.org/
    [2] https://en.wikipedia.org/wiki/The_lexer_hack
    [3] https://raw.githubusercontent.com/gcc-mirror/gcc/master/gcc/c/
    c-parser.c

    [4] https://github.com/libfirm/cparser/blob/
    0cc43ed4bb4d475728583eadcf9e9726682a838b/src/parser/parser.c
    """
    logger = logging.getLogger('cparser')
    LEFT_ASSOCIATIVE = 'left-associative'
    RIGHT_ASSOCIATIVE = 'right-associative'

    def __init__(self, context, semantics):
        super().__init__()
        self.context = context
        self.semantics = semantics
        self.type_qualifiers = {'volatile', 'const'}
        self.storage_classes = {
            'typedef', 'static', 'extern', 'register', 'auto'}
        self.type_specifiers = {
            'void', 'char', 'int', 'float', 'double',
            'short', 'long', 'signed', 'unsigned'}

        self.keywords = {
            'true', 'false',
            'else', 'if', 'while', 'do', 'for', 'return', 'goto',
            'switch', 'case', 'default', 'break', 'continue',
            'sizeof', 'struct', 'union', 'enum'}

        # Some additions from C99:
        if self.context.coptions['std'] == 'c99':
            self.type_qualifiers.add('restrict')
            self.keywords.add('inline')

        # Complete the set of keywords:
        self.keywords |= self.storage_classes
        self.keywords |= self.type_qualifiers
        self.keywords |= self.type_specifiers

        # Define a priority map for operators:
        self.prio_map = {
            ',': (self.LEFT_ASSOCIATIVE, 3),
            '=': (self.RIGHT_ASSOCIATIVE, 10),
            '+=': (self.RIGHT_ASSOCIATIVE, 10),
            '-=': (self.RIGHT_ASSOCIATIVE, 10),
            '*=': (self.RIGHT_ASSOCIATIVE, 10),
            '/=': (self.RIGHT_ASSOCIATIVE, 10),
            '%=': (self.RIGHT_ASSOCIATIVE, 10),
            '>>=': (self.RIGHT_ASSOCIATIVE, 10),
            '<<=': (self.RIGHT_ASSOCIATIVE, 10),
            '|=': (self.RIGHT_ASSOCIATIVE, 10),
            '&=': (self.RIGHT_ASSOCIATIVE, 10),
            '^=': (self.RIGHT_ASSOCIATIVE, 10),
            # '++': (LEFT_ASSOCIATIVE, 50),
            # '--': (LEFT_ASSOCIATIVE, 50),
            '?': (self.LEFT_ASSOCIATIVE, 17),
            '||': (self.LEFT_ASSOCIATIVE, 20),
            '&&': (self.LEFT_ASSOCIATIVE, 30),
            '|': (self.LEFT_ASSOCIATIVE, 40),
            '^': (self.LEFT_ASSOCIATIVE, 50),
            '&': (self.LEFT_ASSOCIATIVE, 60),
            '<': (self.LEFT_ASSOCIATIVE, 70),
            '<=': (self.LEFT_ASSOCIATIVE, 70),
            '>': (self.LEFT_ASSOCIATIVE, 70),
            '>=': (self.LEFT_ASSOCIATIVE, 70),
            '!=': (self.LEFT_ASSOCIATIVE, 70),
            '==': (self.LEFT_ASSOCIATIVE, 70),
            '>>': (self.LEFT_ASSOCIATIVE, 80),
            '<<': (self.LEFT_ASSOCIATIVE, 80),
            '+': (self.LEFT_ASSOCIATIVE, 90),
            '-': (self.LEFT_ASSOCIATIVE, 90),
            '*': (self.LEFT_ASSOCIATIVE, 100),
            '/': (self.LEFT_ASSOCIATIVE, 100),
            '%': (self.LEFT_ASSOCIATIVE, 100),
        }

        # Set work variables:
        self.typedefs = set()

    # Entry points:
    def parse(self, tokens):
        """ Here the parsing of C is begun ...

        Parse the given tokens.
        """
        self.logger.debug('Parsing some nice C code!')
        self.init_lexer(tokens)
        self.typedefs = set()
        self.typedefs.add('__builtin_va_list')
        cu = self.parse_translation_unit()
        self.logger.info('Parsing finished')
        return cu

    def parse_translation_unit(self):
        """ Top level start of parsing """
        self.semantics.begin()
        while not self.at_end:
            for declaration in self.parse_declarations():
                # print('decl', declaration)
                self.semantics.add_global_declaration(declaration)
        return self.semantics.finish_compilation_unit()

    # Declarations part:
    def parse_declarations(self):
        """ Parse normal declarations """
        ds = self.parse_decl_specifiers()
        # TODO: perhaps not parse functions here?
        if self.has_consumed(';'):
            declarations = []
        else:
            declarations = self.parse_decl_group(ds)
        return declarations

    def parse_decl_specifiers(self, allow_storage_class=True):
        """ Parse declaration specifiers.

        At the end we know type, storage class and qualifiers.

        Gathers storage classes:
        - typedef
        - extern
        - static

        One of the following type specifiers:
        - void, char, int, unsigned, long, ...
        - typedef-ed type
        - struct, union or enum

        Type qualifiers:
        - const
        - volatile
        """

        storage_class = None
        type_specifiers = []
        type_qualifiers = set()
        typ = None

        while True:
            if self.peak == 'TYPE-ID':
                # We got a typedef type!
                type_name = self.consume()
                if typ:
                    self.error('Unexpected typename', type_name.loc)
                else:
                    typ = self.semantics.on_typename(
                        type_name.val, type_name.loc)
            elif self.peak in self.type_specifiers:
                type_specifier = self.consume(self.type_specifiers)
                location = type_specifier.loc
                if typ:
                    self.error('Type already determined', type_specifier)
                else:
                    type_specifiers.append(type_specifier.val)
            elif self.peak == 'enum':
                if typ:
                    self.error('Unexpected enum')
                else:
                    typ = self.parse_enum()
            elif self.peak in ['struct', 'union']:
                if typ:
                    self.error('Type already determined')
                else:
                    typ = self.parse_struct_or_union()
            elif self.peak in self.storage_classes:
                klass = self.consume(self.storage_classes)
                if not allow_storage_class:
                    self.error('Unexpected storage class', klass.loc)
                elif storage_class:
                    self.error('Multiple storage classes', klass.loc)
                else:
                    storage_class = klass.val
            elif self.peak in self.type_qualifiers:
                type_qualifier = self.consume(self.type_qualifiers)
                if type_qualifier.val in type_qualifiers:
                    self.error('Double type qualifier', type_qualifier.loc)
                else:
                    type_qualifiers.add(type_qualifier.val)
            elif self.peak in ['inline']:
                self.consume('inline')
                # inline is a compiler hint. For now, ignore this hint :)
                self.logger.debug('Ignoring inline for now')
            else:
                break

        # Now that we are here, the type must be determined
        if not typ and type_specifiers:
            typ = self.semantics.on_basic_type(type_specifiers, location)

        if not typ:
            self.error('Expected at least one type specifier')

        typ = self.semantics.on_type_qualifiers(type_qualifiers, typ)
        ds = nodes.DeclSpec(storage_class, typ)
        return ds

    def parse_struct_or_union(self):
        """ Parse a struct or union """
        keyword = self.consume({'struct', 'union'})

        # We might have an optional tag:
        if self.peak == 'ID':
            tag = self.consume('ID').val
        elif self.peak == '{':
            tag = None
        else:
            print(self.typedefs)
            self.error(
                'Expected tag name or "{{", but got {}'.format(self.peak),
                keyword.loc)

        if self.peak == '{':
            # We have a struct declarations:
            self.consume('{')
            fields = []
            while self.peak != '}':
                ds = self.parse_decl_specifiers(allow_storage_class=False)
                while True:
                    type_modifiers, name = self.parse_type_modifiers(
                        abstract=False)
                    # Handle optional struct field size:
                    if self.peak == ':':
                        self.consume(':')
                        bitsize = self.parse_constant_expression()
                        # TODO: move this somewhere else?
                    else:
                        bitsize = None
                    field = (
                        ds.storage_class, ds.typ, name.val, type_modifiers,
                        bitsize, name.loc)
                    fields.append(field)
                    if self.has_consumed(','):
                        continue
                    else:
                        break
                self.consume(';')
            self.consume('}')
        else:
            fields = None

        return self.semantics.on_struct_or_union(
            keyword.val, tag, fields, keyword.loc)

    def parse_enum(self):
        """ Parse an enum definition """
        keyword = self.consume('enum')

        # We might have an optional tag:
        if self.peak == 'ID':
            tag = self.consume('ID').val
        elif self.peak == '{':
            tag = None
        else:
            self.error(
                'Expected tag name or enum declaration, but got {}'.format(
                    self.peak),
                keyword.loc)

        ctyp = self.semantics.on_enum(tag, keyword.loc)

        # If we have a body, either after tag or directly, parse it:
        if self.peak == '{':
            self.consume('{')
            self.semantics.enter_enum_values(ctyp, keyword.loc)
            while self.peak != '}':
                name = self.consume('ID')
                if self.has_consumed('='):
                    value = self.parse_constant_expression()
                else:
                    value = None
                self.semantics.on_enum_value(ctyp, name.val, value, name.loc)
                if not self.has_consumed(','):
                    break
            self.consume('}')
            self.semantics.exit_enum_values(ctyp, keyword.loc)

        return ctyp

    def parse_decl_group(self, ds):
        """ Parse the rest after the first declaration spec.

        For example we have parsed 'static int' and we will now parse the rest.
        This can be either a function, or a sequence of initializable
        variables. At least it will probably contain some sort of
        identifier and an optional pointer stuff.
        """
        declarations = []
        d = self.parse_declarator()
        if ds.storage_class == 'typedef':
            declarations.append(self.parse_typedef(ds, d))
            while self.has_consumed(','):
                d = self.parse_declarator()
                declarations.append(self.parse_typedef(ds, d))
            self.consume(';')
        elif self.peak == '{':
            # if function, parse implementation.
            # func_def = None
            declarations.append(self.parse_function_declaration(ds, d))
        else:
            # We have variables here
            declarations.append(self.parse_variable_declaration(ds, d))
            while self.has_consumed(','):
                d = self.parse_declarator()
                declarations.append(self.parse_variable_declaration(ds, d))
            self.consume(';')
        return declarations

    def parse_function_declaration(self, ds, d):
        """ Parse a function declaration with implementation """
        function = self.semantics.on_function_declaration(
            ds.storage_class, ds.typ, d.name, d.type_modifiers, d.location)
        self.semantics.enter_function(function)
        body = self.parse_compound_statement()
        # d.body = body
        self.semantics.end_function(body)
        return function

    def parse_variable_declaration(self, ds, d):
        # Create the variable:
        variable = self.semantics.on_variable_declaration(
            ds.storage_class, ds.typ, d.name, d.type_modifiers, d.location)

        # Handle the initial value:
        if self.has_consumed('='):
            initializer = self.parse_variable_initializer()
            self.semantics.on_variable_initialization(variable, initializer)
        return variable

    def parse_typedef(self, ds, d):
        """ Process typedefs """
        self.typedefs.add(d.name)
        return self.semantics.on_typedef(
            ds.typ, d.name, d.type_modifiers, d.location)

    def parse_declarator(self, abstract=False):
        """ Given a declaration specifier, parse the rest.

        This involves parsing optionally pointers and qualifiers
        and next the declaration itself.
        """

        type_modifiers, name = self.parse_type_modifiers(abstract=abstract)
        if name:
            name, location = name.val, name.loc
        else:
            name = location = None

        # Handle typedefs:
        # if ds.storage_class == 'typedef':
        #    assert name is not None
        #    self.typedefs.add(name)
        return nodes.Declarator(name, type_modifiers, location)

    def parse_variable_initializer(self):
        """ Parse the C-style array or struct initializer stuff """
        if self.peak == '{':
            location = self.consume('{').loc
            values = []
            values.append(self.parse_variable_initializer())
            while self.has_consumed(','):
                if self.peak == '}':
                    break
                values.append(self.parse_variable_initializer())
            self.consume('}')
            initializer = self.semantics.on_initializer_list(values, location)
        else:
            if self.peak == '[' and self.options['std'] == 'c99':
                # Parse designators like: int a[10] = {[1]=5, [4]=3, 4}
                self.consume('[')
                index = self.parse_constant_expression()
                self.consume(']')
                self.consume('=')
                initializer = self.parse_constant_expression()
                initializer = (index, initializer)
            else:
                initializer = self.parse_constant_expression()
        return initializer

    def parse_function_arguments(self):
        """ Parse function postfix. We have type and name, now parse
            function arguments """
        # TODO: allow K&R style arguments
        arguments = []
        # self.consume('(')
        if self.peak != ')':
            while True:
                if self.peak == '...':
                    # Variable arguments found!
                    self.consume('...')
                    arguments.append('...')
                    break
                else:
                    ds = self.parse_decl_specifiers()
                    d = self.parse_declarator(
                        abstract=True)
                    arg = self.semantics.on_function_argument(
                        ds.typ, d.name, d.type_modifiers, d.location)
                    arguments.append(arg)
                    if not self.has_consumed(','):
                        break
        # self.consume(')')
        return arguments

    def parse_type_modifiers(self, abstract=False):
        """ Parse the pointer, name and array or function suffixes.

        Can be abstract type, and if so, the type may be nameless.

        The result of all this action is a type modifier list with
        the proper type modifications required by the given code.
        """

        first_modifiers = []
        # Handle the pointer:
        while self.has_consumed('*'):
            type_qualifiers = set()
            while self.peak in self.type_qualifiers:
                type_qualifier = self.consume(self.type_qualifiers)
                if type_qualifier.val in type_qualifiers:
                    self.error('Duplicate type qualifier', type_qualifier)
                else:
                    type_qualifiers.add(type_qualifier.val)
            first_modifiers.append(('POINTER', type_qualifiers))

        # First parse some id, or something else
        middle_modifiers = []
        last_modifiers = []  # TODO: maybe move id detection in seperate part?
        if self.peak == 'ID':
            name = self.consume('ID')
        elif self.peak == '(':
            # May be pointer to function?
            self.consume('(')
            if self.is_declaration_statement():
                # we are faced with function arguments
                arguments = self.parse_function_arguments()
                last_modifiers.append(('FUNCTION', arguments))
                name = None
            else:
                # These are grouped type modifiers.
                sub_modifiers, name = self.parse_type_modifiers(
                    abstract=abstract)
                middle_modifiers.extend(sub_modifiers)
            self.consume(')')
        else:
            if abstract:
                name = None
            else:
                self.error('Expected a name')
            # self.not_impl()
            # raise NotImplementedError(str(self.peak))

        # Now we have name, check for function decl:
        while True:
            if self.peak == '(':
                self.consume('(')
                arguments = self.parse_function_arguments()
                self.consume(')')
                last_modifiers.append(('FUNCTION', arguments))
            elif self.peak == '[':
                # Handle array type suffix:
                self.consume('[')
                if self.peak == '*':
                    # Handle VLA arrays:
                    amount = 'vla'
                elif self.peak == ']':
                    amount = None
                else:
                    amount = self.parse_expression()
                self.consume(']')
                last_modifiers.append(('ARRAY', amount))
            else:
                break

        # Type modifiers: `go right when you can, go left when you must`
        first_modifiers.reverse()
        type_modifiers = middle_modifiers + last_modifiers + first_modifiers
        return type_modifiers, name

    def parse_typename(self):
        """ Parse a type specifier used in sizeof(int) for example. """
        ds = self.parse_decl_specifiers()
        if ds.storage_class:
            self.error('Storage class cannot be used here')
        type_modifiers, name = self.parse_type_modifiers(abstract=True)
        if name:
            self.error('Unexpected name for type declaration', name)
        location = self.current_location
        return self.semantics.on_type(ds.typ, type_modifiers, location)

    # Statement part:
    def parse_statement_or_declaration(self):
        """ Parse either a statement or a declaration

        Returns: a list of statements """

        if self.is_declaration_statement():
            # TODO: do not use current location member.
            location = self.current_location
            statements = []
            for declaration in self.parse_declarations():
                statement = self.semantics.on_declaration_statement(
                    declaration, location)
                statements.append(statement)
        else:
            statements = [self.parse_statement()]
        return statements

    def is_declaration_statement(self):
        """ Determine whether we are facing a declaration or not """
        if self.peak in self.storage_classes:
            return True
        elif self.peak in self.type_qualifiers:
            return True
        elif self.peak in self.type_specifiers:
            return True
        elif self.peak in ('struct', 'union', 'enum', 'TYPE-ID'):
            return True
        else:
            return False

    def parse_statement(self):
        """ Parse a statement """
        m = {
            'for': self.parse_for_statement,
            'if': self.parse_if_statement,
            'do': self.parse_do_statement,
            'while': self.parse_while_statement,
            'switch': self.parse_switch_statement,
            'case': self.parse_case_statement,
            'default': self.parse_default_statement,
            'break': self.parse_break_statement,
            'continue': self.parse_continue_statement,
            'goto': self.parse_goto_statement,
            'return': self.parse_return_statement,
            '{': self.parse_compound_statement,
            ';': self.parse_empty_statement,
            }
        if self.peak in m:
            statement = m[self.peak]()
        else:
            # Expression statement!
            if self.peak == 'ID' and self.look_ahead(1).val == ':':
                statement = self.parse_label()
            else:
                expression = self.parse_expression()
                statement = self.semantics.on_expression_statement(expression)
                self.consume(';')
        return statement

    def parse_label(self):
        """ Parse a label statement """
        name = self.consume('ID')
        self.consume(':')
        statement = self.parse_statement()
        return self.semantics.on_label(name.val, statement, name.loc)

    def parse_empty_statement(self):
        """ Parse a statement that does nothing! """
        location = self.consume(';').loc
        return self.semantics.on_empty(location)

    def parse_compound_statement(self):
        """ Parse a series of statements surrounded by '{' and '}' """
        statements = []
        location = self.consume('{').loc
        self.semantics.enter_compound_statement(location)
        while self.peak != '}':
            statements.extend(self.parse_statement_or_declaration())
        self.consume('}')
        return self.semantics.on_compound_statement(statements, location)

    def parse_if_statement(self):
        """ Parse an if statement """
        location = self.consume('if').loc
        condition = self.parse_condition()
        then_statement = self.parse_statement()
        if self.has_consumed('else'):
            else_statement = self.parse_statement()
        else:
            else_statement = None
        return self.semantics.on_if(
            condition, then_statement, else_statement, location)

    def parse_switch_statement(self):
        """ Parse an switch statement """
        location = self.consume('switch').loc
        self.consume('(')
        expression = self.parse_expression()
        self.consume(')')
        self.semantics.on_switch_enter(expression)
        statement = self.parse_statement()
        return self.semantics.on_switch_exit(expression, statement, location)

    def parse_case_statement(self):
        """ Parse a case """
        location = self.consume('case').loc
        value = self.parse_expression()
        self.consume(':')
        statement = self.parse_statement()
        return self.semantics.on_case(value, statement, location)

    def parse_default_statement(self):
        """ Parse the default case """
        location = self.consume('default').loc
        self.consume(':')
        statement = self.parse_statement()
        return self.semantics.on_default(statement, location)

    def parse_break_statement(self):
        """ Parse a break """
        location = self.consume('break').loc
        self.consume(';')
        return self.semantics.on_break(location)

    def parse_continue_statement(self):
        """ Parse a continue statement """
        location = self.consume('continue').loc
        self.consume(';')
        return self.semantics.on_continue(location)

    def parse_goto_statement(self):
        """ Parse a goto """
        location = self.consume('goto').loc
        label = self.consume('ID').val
        self.consume(';')
        return self.semantics.on_goto(label, location)

    def parse_while_statement(self):
        """ Parse a while statement """
        location = self.consume('while').loc
        condition = self.parse_condition()
        body = self.parse_statement()
        return self.semantics.on_while(condition, body, location)

    def parse_do_statement(self):
        """ Parse a do-while statement """
        location = self.consume('do').loc
        body = self.parse_statement()
        self.consume('while')
        condition = self.parse_condition()
        self.consume(';')
        return self.semantics.on_do(body, condition, location)

    def parse_for_statement(self):
        """ Parse a for statement """
        location = self.consume('for').loc
        self.consume('(')
        if self.peak == ';':
            initial = None
        else:
            initial = self.parse_expression()
        self.consume(';')

        if self.peak == ';':
            condition = None
        else:
            condition = self.parse_expression()
        self.consume(';')

        if self.peak == ')':
            post = None
        else:
            post = self.parse_expression()
        self.consume(')')

        body = self.parse_statement()
        return self.semantics.on_for(initial, condition, post, body, location)

    def parse_return_statement(self):
        """ Parse a return statement """
        location = self.consume('return').loc
        if self.peak == ';':
            value = None
        else:
            value = self.parse_expression()
        self.consume(';')
        return self.semantics.on_return(value, location)

    # Expression parts:
    def parse_condition(self):
        """ Parse an expression between parenthesis """
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        return condition

    def parse_constant_expression(self):
        """ Parse a constant expression """
        return self.parse_binop_with_precedence(17)

    def parse_assignment_expression(self):
        return self.parse_binop_with_precedence(10)

    def parse_expression(self):
        """ Parse an expression.

        See also: http://en.cppreference.com/w/c/language/operator_precedence
        """
        return self.parse_binop_with_precedence(0)

    def parse_binop_with_precedence(self, priority):
        lhs = self.parse_primary_expression()

        # print('prio=', prio, self.peak)
        while self.peak in self.prio_map and \
                self.prio_map[self.peak][1] >= priority:
            op = self.consume()
            op_associativity, op_prio = self.prio_map[op.val]
            if op.val == '?':
                # Eat middle part:
                middle = self.parse_expression()
                self.consume(':')
                rhs = self.parse_binop_with_precedence(op_prio)
                lhs = self.semantics.on_ternop(
                    lhs, op.val, middle, rhs, op.loc)
            else:
                rhs = self.parse_binop_with_precedence(op_prio)
                lhs = self.semantics.on_binop(lhs, op.val, rhs, op.loc)
        return lhs

    def parse_unary_expression(self):
        return self.parse_postfix_expression()

    def parse_postfix_expression(self):
        return self.parse_primary_expression()

    def parse_primary_expression(self):
        """ Parse a primary expression """
        if self.peak == 'ID':
            identifier = self.consume('ID')
            if self.peak == '(':
                # Function call!
                self.consume('(')
                args = []
                while self.peak != ')':
                    args.append(self.parse_assignment_expression())
                    if self.peak != ')':
                        self.consume(',')
                self.consume(')')
                expr = self.semantics.on_call(
                    identifier.val, args, identifier.loc)
            else:
                expr = self.semantics.on_variable_access(
                    identifier.val, identifier.loc)
        elif self.peak == 'NUMBER':
            n = self.consume()
            expr = self.semantics.on_number(n.val, n.loc)
        elif self.peak == 'CHAR':
            n = self.consume()
            expr = self.semantics.on_char(n.val, n.loc)
        elif self.peak == 'STRING':
            txt = self.consume()
            expr = self.semantics.on_string(txt.val, txt.loc)
        elif self.peak in ['!', '*', '+', '-', '~', '&', '--', '++']:
            op = self.consume()
            if op.val in ['--', '++']:
                operator = op.val + 'x'
            else:
                operator = op.val
            expr = self.parse_primary_expression()
            expr = self.semantics.on_unop(operator, expr, op.loc)
        elif self.peak == 'sizeof':
            location = self.consume('sizeof').loc
            if self.peak == '(':
                self.consume('(')
                if self.is_declaration_statement():
                    typ = self.parse_typename()
                else:
                    typ = self.parse_expression()
                self.consume(')')
                expr = self.semantics.on_sizeof(typ, location)
            else:
                sizeof_expr = self.parse_primary_expression()
                expr = self.semantics.on_sizeof(sizeof_expr, location)
        elif self.peak == '(':
            loc = self.consume('(').loc
            # Is this a type cast?
            if self.is_declaration_statement():
                # Cast!
                to_typ = self.parse_typename()
                self.consume(')')
                casted_expr = self.parse_primary_expression()
                expr = self.semantics.on_cast(to_typ, casted_expr, loc)
            else:
                # Parenthized expression (reset precedence)
                expr = self.parse_expression()
                self.consume(')')
        else:
            self.not_impl()

        # Postfix operations (have the highest precedence):
        while self.peak in ['--', '++', '[', '.', '->']:
            if self.peak in ['--', '++']:
                op = self.consume()
                expr = self.semantics.on_unop('x' + op.val, expr, op.loc)
            elif self.peak == '[':
                location = self.consume('[').loc
                index = self.parse_expression()
                self.consume(']')
                expr = self.semantics.on_array_index(expr, index, location)
            elif self.peak == '.':
                location = self.consume('.').loc
                field = self.consume('ID').val
                expr = self.semantics.on_field_select(expr, field, location)
            elif self.peak == '->':
                location = self.consume('->').loc
                field = self.consume('ID').val
                # Dereference pointer:
                expr = self.semantics.on_unop('*', expr, location)
                expr = self.semantics.on_field_select(expr, field, location)
            else:  # pragma: no cover
                self.not_impl()
        return expr

    # Lexer helpers:
    def next_token(self):
        """ Advance to the next token """
        tok = super().next_token()

        # Implement lexer hack here:
        if tok and tok.typ == 'ID' and tok.val in self.typedefs:
            tok.typ = 'TYPE-ID'

        return tok

    @property
    def peak(self):
        """ Look at the next token to parse without popping it """
        if self.token:
            # Also implement lexer hack here:
            if self.token.typ == 'ID' and self.token.val in self.typedefs:
                return 'TYPE-ID'
            return self.token.typ
