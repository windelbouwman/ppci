"""
    This module contains the parsing parts for the c3 language
"""

import logging
from .. import CompilerError
from .astnodes import Member, Literal, TypeCast, Unop, Binop
from .astnodes import Assignment, ExpressionStatement, Compound
from .astnodes import Return, While, If, Empty, For
from .astnodes import FunctionType, Function, FormalParameter
from .astnodes import StructureType, DefinedType, PointerType, ArrayType
from .astnodes import Constant, Variable, Sizeof
from .astnodes import StructField, Deref, Index
from .astnodes import Identifier, FunctionCall


class Parser:
    """ Parses sourcecode into an abstract syntax tree (AST) """
    def __init__(self, diag):
        self.logger = logging.getLogger('c3')
        self.diag = diag

    def parse_source(self, tokens, context):
        """ Parse a module from tokens """
        self.logger.debug('Parsing source')
        self.tokens = tokens
        self.token = self.tokens.__next__()
        try:
            self.parse_module(context)
            self.logger.debug('Parsing complete')
        except CompilerError as ex:
            self.diag.addDiag(ex)
            raise

    def error(self, msg):
        """ Raise an error at the current location """
        raise CompilerError(msg, self.token.loc)

    # Lexer helpers:
    def consume(self, typ):
        """ Assert that the next token is typ, and if so, return it """
        if self.Peak == typ:
            return self.NextToken()
        else:
            self.error('Excected: "{0}", got "{1}"'.format(typ, self.Peak))

    @property
    def Peak(self):
        return self.token.typ

    def has_consumed(self, typ):
        """ Checks if the look-ahead token is of type typ, and if so
            eats the token and returns true """
        if self.Peak == typ:
            self.consume(typ)
            return True
        return False

    def NextToken(self):
        tok = self.token
        if tok.typ != 'EOF':
            self.token = self.tokens.__next__()
        return tok

    def add_declaration(self, decl):
        self.currentPart.add_declaration(decl)

    def parse_module(self, context):
        """ Parse a module definition """
        self.consume('module')
        name = self.consume('ID')
        self.consume(';')
        self.logger.debug('Parsing package {}'.format(name.val))
        self.mod = context.get_module(name.val)  # , name.loc)
        self.currentPart = self.mod
        while self.Peak != 'EOF':
            self.parse_top_level()
        self.consume('EOF')

    def parse_top_level(self):
        """ Parse toplevel declaration """
        if self.Peak == 'function':
            self.parse_function_def()
        elif self.Peak == 'var':
            self.parse_variable_def()
        elif self.Peak == 'const':
            self.parse_const_def()
        elif self.Peak == 'type':
            self.parse_type_def()
        elif self.Peak == 'import':
            self.parse_import()
        else:
            self.error('Expected function, var, const or type')

    def parse_import(self):
        """ Parse import construct """
        self.consume('import')
        name = self.consume('ID').val
        self.mod.imports.append(name)
        self.consume(';')

    def parse_designator(self):
        """ A designator designates an object with a name. """
        name = self.consume('ID')
        return Identifier(name.val, name.loc)

    def parse_id_sequence(self):
        """ Parse a sequence of id's """
        ids = [self.consume('ID')]
        while self.has_consumed(','):
            ids.append(self.consume('ID'))
        return ids

    # Type system
    def parse_type_spec(self):
        """ Parse type specification """
        # Parse the first part of a type spec:
        if self.Peak == 'struct':
            self.consume('struct')
            self.consume('{')
            mems = []
            while self.Peak != '}':
                mem_t = self.parse_type_spec()
                for i in self.parse_id_sequence():
                    mems.append(StructField(i.val, mem_t))
                self.consume(';')
            self.consume('}')
            the_type = StructureType(mems)
        elif self.Peak == 'enum':
            raise NotImplementedError('enum not yet implemented')
        else:
            # The type is identified by an identifier:
            the_type = self.parse_designator()
            while self.has_consumed('.'):
                field = self.consume('ID')
                the_type = Member(the_type, field.val, field.loc)

        # Check for the volatile modifier:
        the_type.volatile = self.has_consumed('volatile')

        # Check for pointer or array suffix:
        while self.Peak in ['*', '[']:
            if self.has_consumed('*'):
                the_type = PointerType(the_type)
            elif self.has_consumed('['):
                if self.Peak == ']':
                    loc = self.consume(']').loc
                    size = Literal(0, loc)
                else:
                    size = self.parse_expression()
                    self.consume(']')
                the_type = ArrayType(the_type, size)
            else:
                raise Exception()
        return the_type

    def parse_type_def(self):
        """ Parse a type definition """
        self.consume('type')
        newtype = self.parse_type_spec()
        typename = self.consume('ID')
        self.logger.debug('Parsing type {}'.format(typename.val))
        self.consume(';')
        typedef = DefinedType(typename.val, newtype, typename.loc)
        self.add_declaration(typedef)

    # Variable declarations:
    def parse_variable_def(self):
        """ Parse variable declaration """
        # TODO handle variable initialization?
        self.consume('var')
        var_type = self.parse_type_spec()
        for name in self.parse_id_sequence():
            var = Variable(name.val, var_type, name.loc)
            self.add_declaration(var)
        self.consume(';')

    def parse_const_def(self):
        """ Parse a constant definition """
        self.consume('const')
        typ = self.parse_type_spec()
        while True:
            name = self.consume('ID')
            self.consume('=')
            val = self.parse_expression()
            constant = Constant(name.val, typ, val, name.loc)
            self.add_declaration(constant)
            if not self.has_consumed(','):
                break
        self.consume(';')

    def parse_variable_or_function_def(self):
        """ Parse either a variable declaration or a function.
            Both functions and variable declarations start with:
            function:
                <type_spec> <name> '('
            variable:
                <type_spec> <name> [',' <name>] ';'
        """
        # TODO
        pass

    def parse_function_def(self):
        """ Parse function definition """
        loc = self.consume('function').loc
        returntype = self.parse_type_spec()
        fname = self.consume('ID').val
        self.logger.debug('Parsing function {}'.format(fname))
        func = Function(fname, loc)
        self.add_declaration(func)
        savePart = self.currentPart
        self.currentPart = func
        self.consume('(')
        parameters = []
        if not self.has_consumed(')'):
            while True:
                typ = self.parse_type_spec()
                name = self.consume('ID')
                param = FormalParameter(name.val, typ, name.loc)
                self.add_declaration(param)
                parameters.append(param)
                if not self.has_consumed(','):
                    break
            self.consume(')')
        paramtypes = [p.typ for p in parameters]
        func.typ = FunctionType(paramtypes, returntype)
        if self.Peak == ';':
            self.consume(';')
            func.body = None
        else:
            func.body = self.parse_compound()
        self.currentPart = savePart

    def parse_if(self):
        """ Parse if statement """
        loc = self.consume('if').loc
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        true_code = self.parse_statement()
        if self.has_consumed('else'):
            false_code = self.parse_statement()
        else:
            false_code = Empty()
        return If(condition, true_code, false_code, loc)

    def parse_while(self):
        """ Parses a while statement """
        loc = self.consume('while').loc
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        statements = self.parse_statement()
        return While(condition, statements, loc)

    def parse_for(self):
        """ Parse a for statement """
        loc = self.consume('for').loc
        self.consume('(')
        init = self.parse_statement()
        self.consume(';')
        condition = self.parse_expression()
        self.consume(';')
        final = self.parse_statement()
        self.consume(')')
        statements = self.parse_statement()
        return For(init, condition, final, statements, loc)

    def parse_return(self):
        """ Parse a return statement """
        loc = self.consume('return').loc
        if self.Peak == ';':
            expr = Literal(0, loc)
        else:
            expr = self.parse_expression()
        self.consume(';')
        return Return(expr, loc)

    def parse_compound(self):
        """ Parse a compound statement, which is bounded by '{' and '}' """
        cb1 = self.consume('{')
        statements = []
        while self.Peak != '}':
            statements.append(self.parse_statement())
        cb2 = self.consume('}')

        # Enforce styling:
        if cb1.loc.col != cb2.loc.col:
            self.error('Braces not in same column!')

        return Compound(statements)

    def parse_statement(self):
        """ Determine statement type based on the pending token """
        if self.Peak == 'if':
            return self.parse_if()
        elif self.Peak == 'while':
            return self.parse_while()
        elif self.Peak == 'for':
            return self.parse_for()
        elif self.Peak == '{':
            return self.parse_compound()
        elif self.has_consumed(';'):
            return Empty()
        elif self.Peak == 'var':
            self.parse_variable_def()
            return Empty()
        elif self.Peak == 'return':
            return self.parse_return()
        else:
            x = self.parse_unary_expression()
            if self.Peak in Assignment.operators:
                # We enter assignment mode here.
                operator = self.Peak
                loc = self.consume(operator).loc
                rhs = self.parse_expression()
                return Assignment(x, rhs, loc, operator)
            else:
                # Must be call statement!
                return ExpressionStatement(x, x.loc)

    # Expression section:
    # We not implement these C constructs:
    # a(2), f = 2
    # and this:
    # a = 2 < x : 4 ? 1;

    def parse_expression(self):
        """ Parse an expression.
            There are some levels of precedence:
            1. logical or
            2. logical and
            3. equality
            4. shift operations
            5. addition and substraction
            6. mul

            # TODO: replace this with 'local binding power'
        """
        lhs = self.parse_logical_and_expression()
        while self.Peak == 'or':
            loc = self.consume('or').loc
            expr_rhs = self.parse_logical_and_expression()
            lhs = Binop(lhs, 'or', expr_rhs, loc)
        return lhs

    def parse_logical_and_expression(self):
        """ Parse sequence of and expressions """
        lhs = self.parse_equality_expression()
        while self.Peak == 'and':
            loc = self.consume('and').loc
            rhs = self.parse_equality_expression()
            lhs = Binop(lhs, 'and', rhs, loc)
        return lhs

    def parse_equality_expression(self):
        """ Parse an value comparison """
        lhs = self.parse_simple_expression()
        while self.Peak in ['<', '==', '>', '>=', '<=', '!=']:
            operation = self.consume(self.Peak)
            rhs = self.parse_simple_expression()
            lhs = Binop(lhs, operation.typ, rhs, operation.loc)
        return lhs

    def parse_simple_expression(self):
        """ Shift operations before + and - ? """
        lhs = self.AddExpression()
        while self.Peak in ['>>', '<<']:
            op = self.consume(self.Peak)
            rhs = self.AddExpression()
            lhs = Binop(lhs, op.typ, rhs, op.loc)
        return lhs

    def AddExpression(self):
        lhs = self.parse_term()
        while self.Peak in ['+', '-']:
            op = self.consume(self.Peak)
            rhs = self.parse_term()
            lhs = Binop(lhs, op.typ, rhs, op.loc)
        return lhs

    def parse_term(self):
        """ Parse a term in an expression """
        lhs = self.parse_bitwise_or()
        while self.Peak in ['*', '/']:
            op = self.consume(self.Peak)
            rhs = self.parse_bitwise_or()
            lhs = Binop(lhs, op.typ, rhs, op.loc)
        return lhs

    def parse_bitwise_or(self):
        """ Parse bitwise or """
        lhs = self.BitwiseAnd()
        while self.Peak == '|':
            op = self.consume(self.Peak)
            rhs = self.BitwiseAnd()
            lhs = Binop(lhs, op.typ, rhs, op.loc)
        return lhs

    def BitwiseAnd(self):
        lhs = self.parse_cast_expression()
        while self.Peak == '&':
            op = self.consume(self.Peak)
            b = self.parse_cast_expression()
            lhs = Binop(lhs, op.typ, b, op.loc)
        return lhs

    # Domain of unary expressions:

    def parse_cast_expression(self):
        """
          the C-style type cast conflicts with '(' expr ')'
          so introduce extra keyword 'cast'
        """
        if self.Peak == 'cast':
            loc = self.consume('cast').loc
            self.consume('<')
            to_type = self.parse_type_spec()
            self.consume('>')
            self.consume('(')
            ce = self.parse_expression()
            self.consume(')')
            return TypeCast(to_type, ce, loc)
        elif self.Peak == 'sizeof':
            # Compiler internal function to determine size of a type
            loc = self.consume('sizeof').loc
            self.consume('(')
            typ = self.parse_type_spec()
            self.consume(')')
            return Sizeof(typ, loc)
        else:
            return self.parse_unary_expression()

    def parse_unary_expression(self):
        """ Handle unary plus, minus and pointer magic """
        if self.Peak in ['&', '*', '-', '+']:
            op = self.consume(self.Peak)
            ce = self.parse_cast_expression()
            if op.val == '*':
                return Deref(ce, op.loc)
            else:
                return Unop(op.typ, ce, op.loc)
        else:
            return self.parse_postfix_expression()

    def parse_postfix_expression(self):
        """ Parse postfix expression """
        pfe = self.parse_primary_expression()
        while self.Peak in ['[', '.', '->', '(']:
            if self.has_consumed('['):
                i = self.parse_expression()
                self.consume(']')
                pfe = Index(pfe, i, i.loc)
            elif self.has_consumed('->'):
                field = self.consume('ID')
                pfe = Deref(pfe, pfe.loc)
                pfe = Member(pfe, field.val, field.loc)
            elif self.has_consumed('.'):
                field = self.consume('ID')
                pfe = Member(pfe, field.val, field.loc)
            elif self.has_consumed('('):
                # Function call
                args = []
                if not self.has_consumed(')'):
                    args.append(self.parse_expression())
                    while self.has_consumed(','):
                        args.append(self.parse_expression())
                    self.consume(')')
                pfe = FunctionCall(pfe, args, pfe.loc)
            else:
                raise Exception()
        return pfe

    def parse_primary_expression(self):
        """ Literal and parenthesis expression parsing """
        if self.has_consumed('('):
            expr = self.parse_expression()
            self.consume(')')
        elif self.Peak == 'NUMBER':
            val = self.consume('NUMBER')
            expr = Literal(val.val, val.loc)
        elif self.Peak == 'REAL':
            val = self.consume('REAL')
            expr = Literal(val.val, val.loc)
        elif self.Peak == 'true':
            val = self.consume('true')
            expr = Literal(True, val.loc)
        elif self.Peak == 'false':
            val = self.consume('false')
            expr = Literal(False, val.loc)
        elif self.Peak == 'STRING':
            val = self.consume('STRING')
            expr = Literal(val.val, val.loc)
        elif self.Peak == 'ID':
            expr = self.parse_designator()
        else:
            self.error('Expected NUM, ID or (expr), got {0}'.format(self.Peak))
        return expr
