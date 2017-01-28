""" A recursive descent pascal parser. """

import logging
from ...common import CompilerError
from ...pcc.recursivedescent import RecursiveDescentParser
from . import nodes
# from .scope import Scope


class Parser(RecursiveDescentParser):
    """ Parses pascal into ast-nodes """
    logger = logging.getLogger('pascal')

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
            module = self.parse_program(context)
            self.logger.debug('Parsing complete')
        except CompilerError as ex:
            self.diag.add_diag(ex)
            raise
        return module

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
        # self.mod = context.get_module(name.val)
        # self.current_scope = self.mod.inner_scope
        self.parse_block()
        self.consume('.')
        self.consume('EOF')
        return self.mod

    def parse_block(self):
        """ Parse a block.

        A block being constants, types, variables and statements.
        """

        # Handle a toplevel construct
        if self.peak == 'const':
            self.parse_constant_definitions()
        if self.peak == 'type':
            self.parse_type_definitions()
        if self.peak == 'var':
            self.parse_variable_declarations()
        if self.peak == 'aaaaaaaaaaaaaaa':
            self.parse_function_declarations()
        self.parse_compound_statement()

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

    def parse_import(self):
        """ Parse import construct """
        self.consume('import')
        name = self.consume('ID').val
        self.mod.imports.append(name)
        self.consume(';')

    def parse_designator(self):
        """ A designator designates an object with a name. """
        name = self.consume('ID')
        return nodes.Identifier(name.val, self.current_scope, name.loc)

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
        if self.peak == 'struct':
            self.consume('struct')
            self.consume('{')
            mems = []
            while self.peak != '}':
                mem_t = self.parse_type_spec()
                for i in self.parse_id_sequence():
                    mems.append(nodes.StructField(i.val, mem_t))
                self.consume(';')
            self.consume('}')
            the_type = nodes.StructureType(mems)
        elif self.peak == 'enum':
            raise NotImplementedError('enum not yet implemented')
        else:
            # The type is identified by an identifier:
            the_type = self.parse_designator()
            while self.has_consumed('.'):
                field = self.consume('ID')
                the_type = nodes.Member(the_type, field.val, field.loc)

        # Check for the volatile modifier (this is a suffix):
        the_type.volatile = self.has_consumed('volatile')

        # Check for pointer or array suffix:
        while self.peak in ['*', '[']:
            if self.has_consumed('*'):
                the_type = nodes.PointerType(the_type)
            elif self.has_consumed('['):
                size = self.parse_expression()
                self.consume(']')
                the_type = nodes.ArrayType(the_type, size)
            else:  # pragma: no cover
                raise RuntimeError()

            # Check (again) for the volatile modifier:
            the_type.volatile = self.has_consumed('volatile')
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

    def parse_variable_def(self, public=True):
        """ Parse variable declaration, optionally with initialization. """
        self.consume('var')
        var_type = self.parse_type_spec()
        variables = []
        while True:
            name = self.consume('ID')
            var = nodes.Variable(name.val, var_type, public, name.loc)
            # Munch initial value:
            if self.peak == '=':
                self.consume('=')
                var.ival = self.parse_const_expression()
            self.add_symbol(var)
            variables.append(var)
            if not self.has_consumed(','):
                break
        self.consume(';')
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

    def parse_switch(self) -> nodes.Switch:
        """ Parse switch statement """
        loc = self.consume('case').loc
        self.consume('(')
        expression = self.parse_expression()
        self.consume(')')
        self.consume('of')
        options = []
        while self.peak != '}':
            if self.peak not in ['case', 'default']:
                self.error('Expected case or default')
            if self.peak == 'case':
                self.consume('case')
                value = self.parse_expression()
            else:
                self.consume('default')
                value = None
            self.consume(':')
            statement = self.parse_statement()
            options.append((value, statement))
        self.consume('end')
        return nodes.Switch(expression, options, loc)

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
        self.parse_identifier()
        self.consume(':=')
        start = self.parse_expression()
        if self.peak == 'to':
            self.consume('to')
            up = True
        else:
            self.consume('downto')
            up = False
        stop = self.parse_expression()
        self.consume('do')
        statement = self.parse_statement()
        return nodes.For(start, up, stop, statement, loc)

    def parse_read(self):
        """ Parses a read statement """
        loc = self.consume('read').loc
        self.consume('(')
        p = self.parse_expression()
        self.consume(')')
        parameters = [p]
        return nodes.Read(parameters, loc)

    def parse_readln(self):
        """ Parses a readln statement """
        loc = self.consume('readln').loc
        self.consume('(')
        p = self.parse_expression()
        self.consume(')')
        parameters = [p]
        return nodes.Readln(parameters, loc)

    def parse_write(self):
        """ Parses a write statement """
        loc = self.consume('write').loc
        self.consume('(')
        p = self.parse_expression()
        self.consume(')')
        parameters = [p]
        return nodes.Write(parameters, loc)

    def parse_writeln(self):
        """ Parses a writeln statement """
        loc = self.consume('writeln').loc
        self.consume('(')
        p = self.parse_expression()
        self.consume(')')
        parameters = [p]
        return nodes.Writeln(parameters, loc)

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
        self.consume('begin')
        statements = []
        statements.append(self.parse_statement())
        while self.has_consumed(';'):
            statements.append(self.parse_statement())
        self.consume('end')

        return nodes.Compound(statements)

    def parse_statement(self) -> nodes.Statement:
        """ Determine statement type based on the pending token """
        if self.peak == 'if':
            return self.parse_if()
        elif self.peak == 'while':
            return self.parse_while()
        elif self.peak == 'repeat':
            return self.parse_repeat()
        elif self.peak == 'for':
            return self.parse_for()
        elif self.peak == 'goto':
            return self.parse_goto()
        elif self.peak == 'case':
            return self.parse_switch()
        elif self.peak == 'read':
            return self.parse_read()
        elif self.peak == 'readln':
            return self.parse_readln()
        elif self.peak == 'write':
            return self.parse_write()
        elif self.peak == 'writeln':
            return self.parse_writeln()
        elif self.peak == 'return':
            return self.parse_return()
        else:
            expression = self.parse_unary_expression()
            if self.peak in nodes.Assignment.operators:
                # We enter assignment mode here.
                operator = self.peak
                loc = self.consume(operator).loc
                rhs = self.parse_expression()
                return nodes.Assignment(expression, rhs, loc, operator)
            else:
                # Must be call statement!
                return nodes.ExpressionStatement(expression, expression.loc)

    def parse_expression(self) -> nodes.Expression:
        lhs = self.parse_simple_expression()
        while self.peak in ['=', '<>', '>', '<', '<=', '>=']:
            operator = self.consume()
            rhs = self.parse_simple_expression()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_simple_expression(self) -> nodes.Expression:
        """ Parse [-] term [-/+ term]* """
        if self.peak in ['+', '-']:
            operator = self.consume()
            lhs = self.parse_term()
            lhs = nodes.Unop(operator.typ, lhs, operator.loc)
        else:
            lhs = self.parse_term()

        while self.peak in ['+', '-']:
            operator = self.consume()
            rhs = self.parse_term()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_term(self):
        """ Parse a term (one or more factors) """
        lhs = self.parse_factor()
        while self.peak in ['*']:
            operator = self.consume()
            rhs = self.parse_factor()
            lhs = nodes.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    def parse_factor(self) -> nodes.Expression:
        """ Parse a factor """
        pfe = self.parse_primary_expression()
        while self.peak in ['[', '.', '->', '(']:
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
        if self.peak == '(':
            self.consume('(')
            expr = self.parse_expression()
            self.consume(')')
        elif self.peak == 'NUMBER':
            val = self.consume('NUMBER')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peak == 'REAL':
            val = self.consume('REAL')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peak == 'true':
            val = self.consume('true')
            expr = nodes.Literal(True, val.loc)
        elif self.peak == 'false':
            val = self.consume('false')
            expr = nodes.Literal(False, val.loc)
        elif self.peak == 'STRING':
            val = self.consume('STRING')
            expr = nodes.Literal(val.val, val.loc)
        elif self.peak == 'ID':
            expr = self.parse_designator()
        else:
            self.error('Expected NUM, ID or (expr), got {0}'.format(self.peak))
        return expr
