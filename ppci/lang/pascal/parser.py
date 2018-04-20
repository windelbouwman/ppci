""" A recursive descent pascal parser. """

import logging
from ...common import CompilerError
from ..tools.recursivedescent import RecursiveDescentParser
from . import nodes
from .symbol_table import Scope


class Parser(RecursiveDescentParser):
    """ Parses pascal into ast-nodes """
    logger = logging.getLogger('pascal.parser')

    def __init__(self, diag):
        super().__init__()
        self.diag = diag
        self.current_scope = None
        self.mod = None

    def parse_source(self, tokens, context):
        """ Parse a module from tokens """
        self.logger.debug('Parsing source')
        self.init_lexer(tokens)
        try:
            program = self.parse_program(context)
        except CompilerError as ex:
            self.diag.add_diag(ex)
            raise
        self.logger.debug('Parsing complete')
        context.add_program(program)
        return program

    def add_symbol(self, sym):
        """ Add a symbol to the current scope """
        if self.current_scope.has_symbol(sym.name, include_parent=False):
            self.error('Redefinition of {0}'.format(sym.name), loc=sym.loc)
        else:
            self.current_scope.add_symbol(sym)

    def parse_program(self, context):
        """ Parse a program """
        self.consume('program')
        name = self.consume('ID')
        self.consume(';')
        self.logger.debug('Parsing program %s', name.val)
        scope = Scope(context.root_scope)
        program = nodes.Program(name.val, scope, name.loc)
        self.current_scope = scope
        main_code = self.parse_block()
        program.main_code = main_code
        self.consume('.')
        self.consume('EOF')
        return program

    def parse_block(self):
        """ Parse a block.

        A block being constants, types, variables and statements.
        """

        # Handle a toplevel construct
        if self.peek == 'const':
            self.parse_constant_definitions()
        if self.peek == 'type':
            self.parse_type_definitions()
        if self.peek == 'var':
            self.parse_variable_declarations()
        if self.peek == 'aaaaaaaaaaaaaaa':
            self.parse_function_declarations()
        return self.parse_compound_statement()

    def parse_constant_definitions(self):
        """ Parse constant definitions """
        self.consume('const')
        typ = self.parse_type_spec()
        while True:
            name = self.consume('ID')
            self.consume('=')
            val = self.parse_expression()
            constant = nodes.Constant(name.val, typ, val, name.loc)
            self.add_symbol(constant)
            if not self.has_consumed(','):
                break
        self.consume(';')

    def parse_uses(self):
        """ Parse import construct """
        self.consume('uses')
        self.consume('ID').val
        # self.mod.imports.append(name)
        self.consume(';')

    def parse_designator(self):
        """ A designator designates an object with a name. """
        name = self.consume('ID')
        # Look it up!
        if self.current_scope.has_symbol(name.val):
            symbol = self.current_scope.get_symbol(name.val)
            return symbol, name.loc
        else:
            self.error('Unknown identifier {}'.format(name.val), name.loc)

    def parse_id_sequence(self):
        """ Parse a sequence of id's """
        ids = [self.consume('ID')]
        while self.has_consumed(','):
            ids.append(self.consume('ID'))
        return ids

    # Type system
    def parse_type_spec(self):
        """ Parse type specification. Type specs are read from right to left.

        A variable spec is given by:
        var [typeSpec] [modifiers] [pointer/array suffix] variable_name

        For example:
        var int volatile * ptr;
        creates a pointer to a volatile integer.
        """
        # Parse the first part of a type spec:
        if self.peek == 'struct':
            self.consume('struct')
            self.consume('{')
            mems = []
            while self.peek != '}':
                mem_t = self.parse_type_spec()
                for i in self.parse_id_sequence():
                    mems.append(nodes.StructField(i.val, mem_t))
                self.consume(';')
            self.consume('}')
            the_type = nodes.StructureType(mems)
        else:
            # The type is identified by an identifier:
            the_type, _ = self.parse_designator()
            # while self.has_consumed('.'):
            #    field = self.consume('ID')
            #    the_type = nodes.Member(the_type, field.val, field.loc)

        # Check for pointer or array suffix:
        while self.peek in ['*', '[']:
            if self.has_consumed('*'):
                the_type = nodes.PointerType(the_type)
            elif self.has_consumed('['):
                size = self.parse_expression()
                self.consume(']')
                the_type = nodes.ArrayType(the_type, size)
            else:  # pragma: no cover
                raise RuntimeError()

        return the_type

    def parse_type_def(self, public=True):
        """ Parse a type definition """
        self.consume('type')
        newtype = self.parse_type_spec()
        typename = self.consume('ID')
        self.consume(';')
        typedef = nodes.DefinedType(
            typename.val, newtype, public, typename.loc)
        self.add_symbol(typedef)

    def parse_variable_declarations(self):
        """ Parse variable declarations """
        self.consume('var')
        variables = []
        variables.extend(self.parse_single_variable_declaration())
        while self.peek == 'ID':
            variables.extend(self.parse_single_variable_declaration())
        return variables

    def parse_single_variable_declaration(self):
        """ Parse a single variable declaration line ending in ';' """
        names = []
        name = self.consume('ID')
        names.append(name)
        while self.has_consumed(','):
            name = self.consume('ID')
            names.append(name)
        self.consume(':')
        var_type = self.parse_type_spec()

        # Initial value:
        if self.has_consumed('='):
            initial = self.parse_expression()
        else:
            initial = None
        self.logger.error('TODO use %s', initial)
        self.consume(';')

        # Create variables:
        variables = []
        for name in names:
            var = nodes.Variable(name.val, var_type, name.loc)
            variables.append(var)
            self.current_scope.add_symbol(var)
        return variables

    def parse_function_def(self, public=True):
        """ Parse function definition """
        loc = self.consume('function').loc
        returntype = self.parse_type_spec()
        fname = self.consume('ID').val
        self.logger.debug('Parsing function %s', fname)
        func = nodes.Function(fname, public, loc)
        self.add_symbol(func)
        # func.inner_scope = Scope(self.current_scope)
        func.package = self.mod
        self.current_scope = func.inner_scope
        self.consume('(')
        parameters = []
        if not self.has_consumed(')'):
            while True:
                typ = self.parse_type_spec()
                name = self.consume('ID')
                param = nodes.FormalParameter(name.val, typ, name.loc)
                self.add_symbol(param)
                parameters.append(param)
                if not self.has_consumed(','):
                    break
            self.consume(')')
        paramtypes = [p.typ for p in parameters]
        func.typ = nodes.FunctionType(paramtypes, returntype)
        func.parameters = parameters
        if self.has_consumed(';'):
            func.body = None
        else:
            func.body = self.parse_compound()
        self.current_scope = self.current_scope.parent

    def parse_if(self):
        """ Parse if statement """
        loc = self.consume('if').loc
        condition = self.parse_expression()
        self.consume('then')
        true_code = self.parse_statement()
        if self.has_consumed('else'):
            false_code = self.parse_statement()
        else:
            false_code = nodes.Empty()
        return nodes.If(condition, true_code, false_code, loc)

    def parse_case_of(self) -> nodes.CaseOf:
        """ Parse case-of statement """
        loc = self.consume('case').loc
        self.consume('(')
        expression = self.parse_expression()
        self.consume(')')
        self.consume('of')
        options = []
        while self.peek not in ['end', 'else']:
            value = self.parse_expression()
            values = [value]
            while self.has_consumed(','):
                value = self.parse_expression()
                values.append(value)

            self.consume(':')
            statement = self.parse_statement()
            self.consume(';')
            options.append((values, statement))

        # Optional else clause:
        if self.peek == 'else':
            self.consume('else')
            default_statement = self.parse_statement()
            self.consume(';')
            options.append(('else', default_statement))

        self.consume('end')
        return nodes.CaseOf(expression, options, loc)

    def parse_while(self) -> nodes.While:
        """ Parses a while statement """
        loc = self.consume('while').loc
        condition = self.parse_expression()
        self.consume('do')
        statement = self.parse_statement()
        return nodes.While(condition, statement, loc)

    def parse_repeat(self):
        """ Parses a repeat statement """
        loc = self.consume('repeat').loc
        statement = self.parse_statement()
        self.consume('until')
        condition = self.parse_expression()
        return nodes.Repeat(statement, condition, loc)

    def parse_for(self) -> nodes.For:
        """ Parse a for statement """
        loc = self.consume('for').loc
        loop_var, _ = self.parse_designator()
        assert isinstance(loop_var, nodes.Variable)
        self.consume(':=')
        start = self.parse_expression()
        if self.peek == 'to':
            self.consume('to')
            up = True
        else:
            self.consume('downto')
            up = False
        stop = self.parse_expression()
        self.consume('do')
        statement = self.parse_statement()
        return nodes.For(loop_var, start, up, stop, statement, loc)

    def parse_read(self):
        """ Parses a read statement """
        loc = self.consume('read').loc
        parameters = self.parse_actual_parameter_list()
        return nodes.Read(parameters, loc)

    def parse_readln(self):
        """ Parses a readln statement """
        loc = self.consume('readln').loc
        parameters = self.parse_actual_parameter_list()
        return nodes.Readln(parameters, loc)

    def parse_write(self):
        """ Parses a write statement """
        loc = self.consume('write').loc
        parameters = self.parse_actual_parameter_list()
        return nodes.Write(parameters, loc)

    def parse_writeln(self):
        """ Parses a writeln statement """
        loc = self.consume('writeln').loc
        parameters = self.parse_actual_parameter_list()
        return nodes.Writeln(parameters, loc)

    def parse_actual_parameter_list(self):
        """ Parse a list of parameters """
        self.consume('(')
        parameters = []
        p = self.parse_expression()
        parameters.append(p)
        while self.has_consumed(','):
            p = self.parse_expression()
            parameters.append(p)
        self.consume(')')
        return parameters

    def parse_return(self) -> nodes.Return:
        """ Parse a return statement """
        loc = self.consume('return').loc
        if self.has_consumed(';'):
            return nodes.Return(None, loc)
        else:
            expr = self.parse_expression()
            self.consume(';')
            return nodes.Return(expr, loc)

    def parse_compound_statement(self):
        """ Parse a compound statement """
        loc = self.consume('begin').loc
        statements = []
        statements.append(self.parse_statement())
        while self.has_consumed(';'):
            statements.append(self.parse_statement())
        self.consume('end')

        return nodes.Compound(statements, loc)

    def parse_statement(self) -> nodes.Statement:
        """ Determine statement type based on the pending token """
        if self.peek == 'if':
            return self.parse_if()
        elif self.peek == 'while':
            return self.parse_while()
        elif self.peek == 'repeat':
            return self.parse_repeat()
        elif self.peek == 'for':
            return self.parse_for()
        elif self.peek == 'goto':
            return self.parse_goto()
        elif self.peek == 'case':
            return self.parse_case_of()
        elif self.peek == 'read':
            return self.parse_read()
        elif self.peek == 'readln':
            return self.parse_readln()
        elif self.peek == 'write':
            return self.parse_write()
        elif self.peek == 'writeln':
            return self.parse_writeln()
        elif self.peek == 'return':
            return self.parse_return()
        elif self.peek == 'begin':
            return self.parse_compound_statement()
        elif self.peek == 'end':
            return nodes.Empty()
        elif self.peek == ';':
            self.consume(';')
            return nodes.Empty()
        elif self.peek == 'ID':
            symbol, loc = self.parse_designator()
            if self.peek == ':=':
                lhs = nodes.VariableAccess(symbol, loc)
                loc = self.consume(':=').loc
                rhs = self.parse_expression()
                return nodes.Assignment(lhs, rhs, loc, ':=')
            else:
                self.not_impl()
        else:
            self.not_impl()
            expression = self.parse_unary_expression()
            if self.peek in nodes.Assignment.operators:
                # We enter assignment mode here.
                operator = self.peek
                loc = self.consume(operator).loc
                rhs = self.parse_expression()
                return nodes.Assignment(expression, rhs, loc, operator)
            else:
                # Must be call statement!
                return nodes.ExpressionStatement(expression, expression.loc)

    def parse_expression(self) -> nodes.Expression:
        lhs = self.parse_simple_expression()
        while self.peek in ['=', '<>', '>', '<', '<=', '>=']:
            operator = self.consume()
            rhs = self.parse_simple_expression()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_simple_expression(self) -> nodes.Expression:
        """ Parse [-] term [-/+ term]* """
        if self.peek in ['+', '-']:
            operator = self.consume()
            lhs = self.parse_term()
            lhs = nodes.Unop(operator.typ, lhs, operator.loc)
        else:
            lhs = self.parse_term()

        while self.peek in ['+', '-']:
            operator = self.consume()
            rhs = self.parse_term()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_term(self):
        """ Parse a term (one or more factors) """
        lhs = self.parse_factor()
        while self.peek in ['*']:
            operator = self.consume()
            rhs = self.parse_factor()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_factor(self) -> nodes.Expression:
        """ Parse a factor """
        pfe = self.parse_primary_expression()
        while self.peek in ['[', '.', '->', '(']:
            if self.has_consumed('['):
                i = self.parse_expression()
                self.consume(']')
                pfe = nodes.Index(pfe, i, i.loc)
            elif self.has_consumed('->'):
                field = self.consume('ID')
                pfe = nodes.Deref(pfe, pfe.loc)
                pfe = nodes.Member(pfe, field.val, field.loc)
            elif self.has_consumed('.'):
                field = self.consume('ID')
                pfe = nodes.Member(pfe, field.val, field.loc)
            elif self.has_consumed('('):
                # Function call
                args = []
                if not self.has_consumed(')'):
                    args.append(self.parse_expression())
                    while self.has_consumed(','):
                        args.append(self.parse_expression())
                    self.consume(')')
                pfe = nodes.FunctionCall(pfe, args, pfe.loc)
            else:  # pragma: no cover
                raise RuntimeError()
        return pfe

    def parse_primary_expression(self) -> nodes.Expression:
        """ Literal and parenthesis expression parsing """
        if self.peek == '(':
            self.consume('(')
            expr = self.parse_expression()
            self.consume(')')
        elif self.peek == 'NUMBER':
            val = self.consume('NUMBER')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peek == 'REAL':
            val = self.consume('REAL')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peek == 'true':
            val = self.consume('true')
            expr = nodes.Literal(True, val.loc)
        elif self.peek == 'false':
            val = self.consume('false')
            expr = nodes.Literal(False, val.loc)
        elif self.peek == 'STRING':
            val = self.consume('STRING')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peek == 'ID':
            symbol, loc = self.parse_designator()
            if isinstance(symbol, nodes.Variable):
                expr = nodes.VariableAccess(symbol, loc)
            else:
                self.not_impl()
        else:
            self.error('Expected NUM, ID or (expr), got {0}'.format(self.peek))
        return expr
