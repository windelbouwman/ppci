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

    def __init__(self, context):
        super().__init__()
        self.context = context
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
        declarations = []
        while not self.at_end:
            declaration = self.parse_external_declaration()
            declarations.append(declaration)

        cu = nodes.CompilationUnit(declarations)
        return cu

    # Declarations part:
    def parse_external_declaration(self):
        return self.parse_function_or_object_decl()

    def parse_function_or_object_decl(self):
        """ Parse a function definition or a list of object declarations """
        ds = self.parse_decl_specifiers()
        if self.has_consumed(';'):
            ds.declarators = []
        else:
            # print(ds)
            ds.declarators = self.parse_decl_group(ds)
        return ds

    def parse_declaration(self):
        """ Parse normal declaration inside function """
        ds = self.parse_decl_specifiers()
        # print(ds)
        # TODO: perhaps not parse functions here?
        if self.has_consumed(';'):
            ds.declarators = []
        else:
            ds.declarators = self.parse_decl_group(ds)
        return ds

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

        ds = nodes.DeclSpec()

        while True:
            if self.peak == 'TYPE-ID':
                # We got a typedef type!
                typ = self.consume()
                if ds.typ:
                    self.error('Type already defined', typ.loc)
                else:
                    ds.typ = nodes.IdentifierType(typ.val, typ.loc)
            elif self.peak in self.type_specifiers:
                type_specifier = self.consume(self.type_specifiers)
                if ds.typ:
                    if isinstance(ds.typ, nodes.BasicType):
                        ds.typ.type_specifiers.append(type_specifier.val)
                    else:
                        self.error('Type already determined', type_specifier)
                else:
                    ds.typ = nodes.BasicType(
                        [type_specifier.val], type_specifier.loc)
            elif self.peak == 'enum':
                if ds.typ:
                    self.error('Type already determined')
                else:
                    ds.typ = self.parse_enum()
            elif self.peak in ['struct', 'union']:
                if ds.typ:
                    self.error('Type already determined')
                else:
                    ds.typ = self.parse_struct_or_union()
            elif self.peak in self.storage_classes:
                storage_class = self.consume(self.storage_classes)
                if not allow_storage_class:
                    self.error('Unexpected storage class', storage_class.loc)
                elif ds.storage_class:
                    self.error('Multiple storage classes', storage_class.loc)
                else:
                    ds.storage_class = storage_class.val
            elif self.peak in self.type_qualifiers:
                type_qualifier = self.consume(self.type_qualifiers)
                if type_qualifier.val in ds.type_qualifiers:
                    self.error('Double type qualifier', type_qualifier.loc)
                else:
                    ds.type_qualifiers.add(type_qualifier.val)
            elif self.peak in ['inline']:
                self.consume('inline')
                # inline is a compiler hint. For now, ignore this hint :)
                self.logger.debug('Ignoring inline for now')
            else:
                break

        # Now that we are here, the type must be determined
        if not ds.typ:
            self.error('Expected at least one type specifier')

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
            self.error('Expected tag name or "{"', keyword.loc)

        if self.peak == '{':
            # We have a struct declarations:
            self.consume('{')
            fields = []
            while self.peak != '}':
                ds = self.parse_decl_specifiers(allow_storage_class=False)
                while True:
                    declarator = self.parse_struct_field_declarator(ds)
                    ds.declarators.append(declarator)
                    if self.has_consumed(','):
                        continue
                    else:
                        break
                fields.append(ds)
                self.consume(';')
            self.consume('}')
        else:
            fields = None

        mp = {'struct': nodes.Struct, 'union': nodes.Union}
        klass = mp[keyword.val]
        return klass(tag, fields, keyword.loc)

    def parse_enum(self):
        """ Parse an enum definition """
        keyword = self.consume('enum')

        # We might have an optional tag:
        if self.peak == 'ID':
            tag = self.consume('ID').val
        elif self.peak == '{':
            tag = None
        else:
            self.error('Expected tag name or enum declaration', keyword.loc)

        # If we have a body, either after tag or directly, parse it:
        if self.peak == '{':
            self.consume('{')
            if self.has_consumed('}'):
                self.error('Empty enum is not allowed')
            enum_values = []
            while self.peak != '}':
                name = self.consume('ID')
                if self.has_consumed('='):
                    value = self.parse_constant_expression()
                else:
                    value = None
                enum_values.append(nodes.Enumerator(name.val, value, name.loc))
                if not self.has_consumed(','):
                    break
            self.consume('}')
        else:
            enum_values = None

        return nodes.Enum(tag, enum_values, keyword.loc)

    def parse_decl_group(self, ds):
        """ Parse the rest after the first declaration spec.

        For example we have parsed 'static int' and we will now parse the rest.
        This can be either a function, or a sequence of initializable
        variables. At least it will probably contain some sort of
        identifier and an optional pointer stuff.
        """

        declarations = []
        d = self.parse_declarator(ds)
        if self.peak == '{':
            # if function, parse implementation.
            # func_def = None
            body = self.parse_compound_statement()
            d.body = body
            declarations.append(d)
        else:
            # We have variables here
            # print(ds, d)

            declarations.append(d)
            while self.has_consumed(','):
                d = self.parse_declarator(ds)
                declarations.append(d)
                # print(ds, d)
            self.consume(';')
        return declarations

    def parse_declarator(self, ds, abstract=False):
        """ Given a declaration specifier, parse the rest.

        This involves parsing optionally pointers and qualifiers
        and next the declaration itself.
        """
        assert ds.typ is not None

        print(ds)
        type_modifiers, name = self.parse_type_modifiers(abstract=abstract)
        if name:
            name, loc = name.val, name.loc
        else:
            name = None
            loc = None

        # Handle the initial value:
        if self.peak == '=':
            self.consume('=')
            initializer = self.parse_variable_initializer()
        else:
            initializer = None

        # Handle typedefs:
        if ds.storage_class == 'typedef':
            assert name is not None
            self.typedefs.add(name)

        return nodes.Declarator(name, type_modifiers, initializer, loc)

    def parse_variable_initializer(self):
        """ Parse the C-style array or struct initializer stuff """
        if self.peak == '{':
            loc = self.consume('{').loc
            series = []
            series.append(self.parse_variable_initializer())
            while self.has_consumed(','):
                series.append(self.parse_variable_initializer())
            self.consume('}')
            initializer = nodes.InitializerList(series, loc)
        else:
            initializer = self.parse_constant_expression()
        return initializer

    def parse_struct_field_declarator(self, ds):
        """ Given a declaration specifier, parse a struct field. """
        assert ds.typ is not None

        type_modifiers, name = self.parse_type_modifiers(abstract=False)
        name, loc = name.val, name.loc

        # Handle optional struct field size:
        if self.peak == ':':
            self.consume(':')
            bitsize = self.parse_constant_expression()
            # TODO: move this somewhere else?
        else:
            bitsize = None

        return nodes.StructFieldDeclarator(name, type_modifiers, bitsize, loc)

    def parse_function_declarator(self):
        """ Parse function postfix. We have type and name, now parse
            function arguments """
        # TODO: allow K&R style arguments
        args = []
        # self.consume('(')
        if self.peak == ')':
            # No arguments..
            # self.consume(')')
            pass
        else:
            while True:
                if self.peak == '...':
                    # Variable arguments found!
                    self.consume('...')
                    args.append('...')
                    break
                else:
                    ds = self.parse_decl_specifiers()
                    d = self.parse_declarator(ds, abstract=True)
                    ds.declarators.append(d)
                    args.append(ds)
                    if not self.has_consumed(','):
                        break
            # self.consume(')')
        return args

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
                arguments = self.parse_function_declarator()
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
                arguments = self.parse_function_declarator()
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

    def parse_function_definition(self):
        """ Parse a function """
        raise NotImplementedError()
        self.parse_compound_statement()

    def parse_typename(self):
        """ Parse a type specifier """
        ds = self.parse_decl_specifiers()
        if ds.storage_class:
            self.error('Storage class cannot be used here')
        declarator = self.parse_abstract_declarator()
        ds.declarators.append(declarator)
        return ds

    def parse_abstract_declarator(self):
        """ Parse a declarator without a variable name """
        location = self.current_location
        type_modifiers, name = self.parse_type_modifiers(abstract=True)
        if name:
            self.error('Unexpected name for type declaration', name)
        return nodes.Declarator(None, type_modifiers, None, location)

    # Statement part:
    def parse_statement_or_declaration(self):
        """ Parse either a statement or a declaration

        Returns: a list of statements """

        if self.is_declaration_statement():
            location = self.current_location
            declaration = self.parse_declaration()
            statement = nodes.DeclarationStatement(declaration, location)
        else:
            statement = self.parse_statement()
        return statement

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
                statement = nodes.ExpressionStatement(expression)
                self.consume(';')
        return statement

    def parse_label(self):
        """ Parse a label statement """
        name = self.consume('ID')
        self.consume(':')
        statement = self.parse_statement()
        return nodes.Label(name.val, statement, name.loc)

    def parse_empty_statement(self):
        """ Parse a statement that does nothing! """
        loc = self.consume(';').loc
        return nodes.Empty(loc)

    def parse_compound_statement(self):
        """ Parse a series of statements surrounded by '{' and '}' """
        statements = []
        loc = self.consume('{').loc
        while self.peak != '}':
            statements.append(self.parse_statement_or_declaration())
        self.consume('}')
        return nodes.Compound(statements, loc)

    def parse_if_statement(self):
        """ Parse an if statement """
        loc = self.consume('if').loc
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        then_statement = self.parse_statement()
        if self.has_consumed('else'):
            no = self.parse_statement()
        else:
            no = None
        return nodes.If(condition, then_statement, no, loc)

    def parse_switch_statement(self):
        """ Parse an switch statement """
        loc = self.consume('switch').loc
        self.consume('(')
        expression = self.parse_expression()
        self.consume(')')
        statement = self.parse_statement()
        return nodes.Switch(expression, statement, loc)

    def parse_case_statement(self):
        """ Parse a case """
        loc = self.consume('case').loc
        value = self.parse_expression()
        self.consume(':')
        statement = self.parse_statement()
        return nodes.Case(value, statement, loc)

    def parse_default_statement(self):
        """ Parse the default case """
        loc = self.consume('default').loc
        self.consume(':')
        statement = self.parse_statement()
        return nodes.Default(statement, loc)

    def parse_break_statement(self):
        """ Parse a break """
        loc = self.consume('break').loc
        self.consume(';')
        return nodes.Break(loc)

    def parse_continue_statement(self):
        """ Parse a continue statement """
        loc = self.consume('continue').loc
        self.consume(';')
        return nodes.Continue(loc)

    def parse_goto_statement(self):
        """ Parse a goto """
        loc = self.consume('goto').loc
        label = self.consume('ID').val
        self.consume(';')
        return nodes.Goto(label, loc)

    def parse_while_statement(self):
        """ Parse a while statement """
        loc = self.consume('while').loc
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        body = self.parse_statement()
        return nodes.While(condition, body, loc)

    def parse_do_statement(self):
        """ Parse a do-while statement """
        loc = self.consume('do').loc
        body = self.parse_statement()
        self.consume('while')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        self.consume(';')
        return nodes.DoWhile(body, condition, loc)

    def parse_for_statement(self):
        """ Parse a for statement """
        loc = self.consume('for').loc
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
        return nodes.For(initial, condition, post, body, loc)

    def parse_return_statement(self):
        """ Parse a return statement """
        loc = self.consume('return').loc
        if self.peak == ';':
            value = None
        else:
            value = self.parse_expression()
        self.consume(';')
        return nodes.Return(value, loc)

    # Expression parts:
    def parse_constant_expression(self):
        """ Parse a constant expression """
        return self.parse_binop_with_precedence(17)

    def parse_assignment_expression(self):
        return self.parse_binop_with_precedence(10)

    def parse_expression(self):
        """ Parse an expression """
        return self.parse_binop_with_precedence(0)

    def parse_binop_with_precedence(self, prio):
        lhs = self.parse_primary_expression()

        # print('prio=', prio, self.peak)
        while self.peak in self.prio_map and \
                self.prio_map[self.peak][1] >= prio:
            op = self.consume()
            op_associativity, op_prio = self.prio_map[op.val]
            if op.val == '?':
                # Eat middle part:
                middle = self.parse_expression()
                self.consume(':')
            rhs = self.parse_binop_with_precedence(op_prio)

            if op.val == '?':
                lhs = nodes.Ternop(lhs, op.val, middle, rhs, op.loc)
            else:
                lhs = nodes.Binop(lhs, op.val, rhs, op.loc)
            # print(lhs)
        return lhs

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
                expr = nodes.FunctionCall(identifier.val, args, identifier.loc)
            else:
                expr = nodes.VariableAccess(identifier.val, identifier.loc)
        elif self.peak == 'NUMBER':
            n = self.consume()
            expr = nodes.NumericLiteral(n.val, n.loc)
        elif self.peak == 'CHAR':
            n = self.consume()
            expr = nodes.CharLiteral(n.val, n.loc)
        elif self.peak == 'STRING':
            txt = self.consume()
            expr = nodes.StringLiteral(txt.val, txt.loc)
        elif self.peak in ['!', '*', '+', '-', '~', '&', '--', '++']:
            op = self.consume()
            if op.val in ['--', '++']:
                operator = op.val + 'x'
            else:
                operator = op.val
            expr = self.parse_primary_expression()
            expr = nodes.Unop(operator, expr, op.loc)
        elif self.peak == 'sizeof':
            loc = self.consume('sizeof').loc
            if self.peak == '(':
                self.consume('(')
                if self.is_declaration_statement():
                    typ = self.parse_typename()
                else:
                    typ = self.parse_expression()
                self.consume(')')
                expr = nodes.Sizeof(typ, loc)
            else:
                sizeof_expr = self.parse_primary_expression()
                expr = nodes.Sizeof(sizeof_expr, loc)
        elif self.peak == '(':
            loc = self.consume('(').loc
            # Is this a type cast?
            if self.is_declaration_statement():
                # Cast!
                to_typ = self.parse_typename()
                self.consume(')')
                casted_expr = self.parse_expression()
                expr = nodes.Cast(to_typ, casted_expr, loc)
            else:
                expr = self.parse_expression()
                self.consume(')')
        else:
            self.not_impl()

        # Postfix operations:
        while self.peak in ['--', '++', '[', '.', '->']:
            if self.peak in ['--', '++']:
                op = self.consume()
                expr = nodes.Unop('x' + op.val, expr, op.loc)
            elif self.peak == '[':
                loc = self.consume('[').loc
                index = self.parse_expression()
                self.consume(']')
                expr = nodes.ArrayIndex(expr, index, loc)
            elif self.peak == '.':
                loc = self.consume('.').loc
                field = self.consume('ID').val
                expr = nodes.FieldSelect(expr, field, loc)
            elif self.peak == '->':
                loc = self.consume('->').loc
                field = self.consume('ID').val
                expr = nodes.Unop('*', expr, loc)  # Dereference pointer
                expr = nodes.FieldSelect(expr, field, loc)
            else:  # pragma: no cover
                self.not_impl()
        return expr

    # Lexer helpers:
    def next_token(self):
        """ Advance to the next token """
        tok = super().next_token()
        # print('parse', tok)

        # Implement lexer hack here:
        if tok and tok.typ == 'ID' and tok.val in self.typedefs:
            tok.typ = 'TYPE-ID'

        # print('parse', tok)
        return tok

    @property
    def peak(self):
        """ Look at the next token to parse without popping it """
        if self.token:
            # Also implement lexer hack here:
            if self.token.typ == 'ID' and self.token.val in self.typedefs:
                return 'TYPE-ID'
            return self.token.typ
