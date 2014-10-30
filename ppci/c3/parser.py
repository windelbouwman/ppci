import logging
from .. import CompilerError
from .astnodes import Member, Literal, TypeCast, Unop, Binop
from .astnodes import Assignment, ExpressionStatement, Compound
from .astnodes import Return, While, If, Empty, For
from .astnodes import FunctionType, Function, FormalParameter
from .astnodes import StructureType, DefinedType, PointerType, ArrayType
from .astnodes import Constant, Variable, Sizeof
from .astnodes import StructField, Deref, Index
from .astnodes import Package
from .astnodes import Identifier
from .astnodes import FunctionCall


class Parser:
    """ Parses sourcecode into an abstract syntax tree (AST) """
    def __init__(self, diag):
        self.logger = logging.getLogger('c3')
        self.diag = diag

    def parseSource(self, tokens):
        self.logger.debug('Parsing source')
        self.tokens = tokens
        self.token = self.tokens.__next__()
        try:
            self.parse_package()
            self.logger.debug('Parsing complete')
            self.mod.ok = True  # Valid until proven wrong :)
            return self.mod
        except CompilerError as e:
            self.diag.addDiag(e)

    def Error(self, msg):
        raise CompilerError(msg, self.token.loc)

    # Lexer helpers:
    def Consume(self, typ):
        if self.Peak == typ:
            return self.NextToken()
        else:
            self.Error('Excected: "{0}", got "{1}"'.format(typ, self.Peak))

    @property
    def Peak(self):
        return self.token.typ

    @property
    def CurLoc(self):
        return self.token.loc

    def hasConsumed(self, typ):
        if self.Peak == typ:
            self.Consume(typ)
            return True
        return False

    def NextToken(self):
        t = self.token
        if t.typ != 'EOF':
            self.token = self.tokens.__next__()
        return t

    def addDeclaration(self, decl):
        self.currentPart.add_declaration(decl)

    def parseImport(self):
        self.Consume('import')
        name = self.Consume('ID').val
        self.mod.imports.append(name)
        self.Consume(';')

    def parse_package(self):
        """ Parse a package definition """
        self.Consume('module')
        name = self.Consume('ID')
        self.Consume(';')
        self.logger.debug('Parsing package {}'.format(name.val))
        self.mod = Package(name.val, name.loc)
        self.currentPart = self.mod
        while self.Peak != 'EOF':
            self.parse_top_level()
        self.Consume('EOF')

    def parse_top_level(self):
        """ Parse toplevel declaration """
        if self.Peak == 'function':
            self.parse_function_def()
        elif self.Peak == 'var':
            self.parse_variable_def()
            # TODO handle variable initialization
        elif self.Peak == 'const':
            self.parseConstDef()
        elif self.Peak == 'type':
            self.parse_type_def()
        elif self.Peak == 'import':
            self.parseImport()
        else:
            self.Error('Expected function, var, const or type')

    def parseDesignator(self):
        """ A designator designates an object with a name. """
        name = self.Consume('ID')
        return Identifier(name.val, name.loc)

    def parseIdSequence(self):
        ids = [self.Consume('ID')]
        while self.hasConsumed(','):
            ids.append(self.Consume('ID'))
        return ids

    # Type system
    def PostFixId(self):
        pfe = self.PrimaryExpression_Id()
        while self.Peak in ['.']:
            if self.hasConsumed('.'):
                field = self.Consume('ID')
                pfe = Member(pfe, field.val, field.loc)
            else:
                raise Exception()
        return pfe

    def PrimaryExpression_Id(self):
        if self.Peak == 'ID':
            return self.parseDesignator()
        self.Error('Expected ID, got {0}'.format(self.Peak))

    def parse_type_spec(self):
        """ Parse type specification """
        if self.Peak == 'struct':
            self.Consume('struct')
            self.Consume('{')
            mems = []
            while self.Peak != '}':
                mem_t = self.parse_type_spec()
                for i in self.parseIdSequence():
                    mems.append(StructField(i.val, mem_t))
                self.Consume(';')
            self.Consume('}')
            theT = StructureType(mems)
        elif self.Peak == 'enum':
            # TODO)
            raise NotImplementedError()
        else:
            theT = self.PostFixId()

        # Check for the volatile modifier:
        theT.volatile = self.hasConsumed('volatile')

        # Check for pointer or array suffix:
        while self.Peak in ['*', '[']:
            if self.hasConsumed('*'):
                theT = PointerType(theT)
            elif self.hasConsumed('['):
                if self.Peak == ']':
                    size = 0
                    self.Consume(']')
                else:
                    size = self.Expression()
                    self.Consume(']')
                theT = ArrayType(theT, size)
            else:
                raise Exception()
        return theT

    def parse_type_def(self):
        self.Consume('type')
        newtype = self.parse_type_spec()
        typename = self.Consume('ID')
        self.logger.debug('Parsing type {}'.format(typename.val))
        self.Consume(';')
        df = DefinedType(typename.val, newtype, typename.loc)
        self.addDeclaration(df)

    # Variable declarations:
    def parse_variable_def(self):
        """ Parse variable declaration """
        self.Consume('var')
        t = self.parse_type_spec()
        for name in self.parseIdSequence():
            v = Variable(name.val, t)
            v.loc = name.loc
            self.addDeclaration(v)
        self.Consume(';')

    def parseConstDef(self):
        self.Consume('const')
        t = self.parse_type_spec()
        while True:
            name = self.Consume('ID')
            self.Consume('=')
            val = self.Expression()
            c = Constant(name.val, t, val)
            self.addDeclaration(c)
            c.loc = name.loc
            if not self.hasConsumed(','):
                break
        self.Consume(';')

    def parse_function_def(self):
        loc = self.Consume('function').loc
        returntype = self.parse_type_spec()
        fname = self.Consume('ID').val
        self.logger.debug('Parsing function {}'.format(fname))
        f = Function(fname, loc)
        self.addDeclaration(f)
        savePart = self.currentPart
        self.currentPart = f
        self.Consume('(')
        parameters = []
        if not self.hasConsumed(')'):
            while True:
                typ = self.parse_type_spec()
                name = self.Consume('ID')
                param = FormalParameter(name.val, typ)
                param.loc = name.loc
                self.addDeclaration(param)
                parameters.append(param)
                if not self.hasConsumed(','):
                    break
            self.Consume(')')
        paramtypes = [p.typ for p in parameters]
        f.typ = FunctionType(paramtypes, returntype)
        if self.Peak == ';':
            self.Consume(';')
            f.body = None
        else:
            f.body = self.parseCompound()
        self.currentPart = savePart

    def parse_if(self):
        loc = self.Consume('if').loc
        self.Consume('(')
        condition = self.Expression()
        self.Consume(')')
        yes = self.Statement()
        no = self.Statement() if self.hasConsumed('else') else Empty()
        return If(condition, yes, no, loc)

    def parse_switch(self):
        loc = self.Consume('switch').loc
        self.Consume('(')
        condition = self.Expression()
        self.Consume(')')
        return Switch(condition, loc)

    def parse_while(self):
        loc = self.Consume('while').loc
        self.Consume('(')
        condition = self.Expression()
        self.Consume(')')
        statements = self.Statement()
        return While(condition, statements, loc)

    def parse_for(self):
        loc = self.Consume('for').loc
        self.Consume('(')
        init = self.Statement()
        self.Consume(';')
        condition = self.Expression()
        self.Consume(';')
        final = self.Statement()
        self.Consume(')')
        statements = self.Statement()
        return For(init, condition, final, statements, loc)

    def parseReturn(self):
        loc = self.Consume('return').loc
        if self.Peak == ';':
            expr = Literal(0, loc)
        else:
            expr = self.Expression()
        self.Consume(';')
        return Return(expr, loc)

    def parseCompound(self):
        self.Consume('{')
        statements = []
        while not self.hasConsumed('}'):
            statements.append(self.Statement())
        return Compound(statements)

    def Statement(self):
        # Determine statement type based on the pending token:
        if self.Peak == 'if':
            return self.parse_if()
        elif self.Peak == 'while':
            return self.parse_while()
        elif self.Peak == 'for':
            return self.parse_for()
        elif self.Peak == 'switch':
            return self.parse_switch()
        elif self.Peak == '{':
            return self.parseCompound()
        elif self.hasConsumed(';'):
            return Empty()
        elif self.Peak == 'var':
            self.parse_variable_def()
            return Empty()
        elif self.Peak == 'return':
            return self.parseReturn()
        else:
            x = self.UnaryExpression()
            if self.Peak == '=':
                # We enter assignment mode here.
                loc = self.Consume('=').loc
                rhs = self.Expression()
                return Assignment(x, rhs, loc)
            else:
                return ExpressionStatement(x, x.loc)

    # Expression section:
    # We not implement these C constructs:
    # a(2), f = 2
    # and this:
    # a = 2 < x : 4 ? 1;

    def Expression(self):
        exp = self.LogicalAndExpression()
        while self.Peak == 'or':
            loc = self.Consume('or').loc
            e2 = self.LogicalAndExpression()
            exp = Binop(exp, 'or', e2, loc)
        return exp

    def LogicalAndExpression(self):
        o = self.EqualityExpression()
        while self.Peak == 'and':
            loc = self.Consume('and').loc
            o2 = self.EqualityExpression()
            o = Binop(o, 'and', o2, loc)
        return o

    def EqualityExpression(self):
        ee = self.SimpleExpression()
        while self.Peak in ['<', '==', '>', '>=', '<=', '!=']:
            op = self.Consume(self.Peak)
            ee2 = self.SimpleExpression()
            ee = Binop(ee, op.typ, ee2, op.loc)
        return ee

    def SimpleExpression(self):
        """ Shift operations before + and - ? """
        e = self.AddExpression()
        while self.Peak in ['>>', '<<']:
            op = self.Consume(self.Peak)
            e2 = self.AddExpression()
            e = Binop(e, op.typ, e2, op.loc)
        return e

    def AddExpression(self):
        e = self.Term()
        while self.Peak in ['+', '-']:
            op = self.Consume(self.Peak)
            e2 = self.Term()
            e = Binop(e, op.typ, e2, op.loc)
        return e

    def Term(self):
        t = self.BitwiseOr()
        while self.Peak in ['*', '/']:
            op = self.Consume(self.Peak)
            t2 = self.BitwiseOr()
            t = Binop(t, op.typ, t2, op.loc)
        return t

    def BitwiseOr(self):
        a = self.BitwiseAnd()
        while self.Peak == '|':
            op = self.Consume(self.Peak)
            b = self.BitwiseAnd()
            a = Binop(a, op.typ, b, op.loc)
        return a

    def BitwiseAnd(self):
        a = self.CastExpression()
        while self.Peak == '&':
            op = self.Consume(self.Peak)
            b = self.CastExpression()
            a = Binop(a, op.typ, b, op.loc)
        return a

    # Domain of unary expressions:

    def CastExpression(self):
        """
          the C-style type cast conflicts with '(' expr ')'
          so introduce extra keyword 'cast'
        """
        if self.Peak == 'cast':
            loc = self.Consume('cast').loc
            self.Consume('<')
            t = self.parse_type_spec()
            self.Consume('>')
            self.Consume('(')
            ce = self.Expression()
            self.Consume(')')
            return TypeCast(t, ce, loc)
        elif self.Peak == 'sizeof':
            return self.sizeof_expression()
        else:
            return self.UnaryExpression()

    def sizeof_expression(self):
        """ Compiler internal function to determine size of a type """
        loc = self.Consume('sizeof').loc
        self.Consume('(')
        typ = self.parse_type_spec()
        self.Consume(')')
        return Sizeof(typ, loc)

    def UnaryExpression(self):
        if self.Peak in ['&', '*']:
            op = self.Consume(self.Peak)
            ce = self.CastExpression()
            if op.val == '*':
                return Deref(ce, op.loc)
            else:
                return Unop(op.typ, ce, op.loc)
        else:
            return self.PostFixExpression()

    def PostFixExpression(self):
        pfe = self.PrimaryExpression()
        while self.Peak in ['[', '.', '->', '(', '++']:
            if self.hasConsumed('['):
                i = self.Expression()
                self.Consume(']')
                pfe = Index(pfe, i, i.loc)
            elif self.hasConsumed('->'):
                field = self.Consume('ID')
                pfe = Deref(pfe, pfe.loc)
                pfe = Member(pfe, field.val, field.loc)
            elif self.hasConsumed('.'):
                field = self.Consume('ID')
                pfe = Member(pfe, field.val, field.loc)
            elif self.Peak == '++':
                loc = self.Consume('++').loc
                pfe = Unop('++', pfe, loc)
            elif self.hasConsumed('('):
                # Function call
                args = []
                if not self.hasConsumed(')'):
                    args.append(self.Expression())
                    while self.hasConsumed(','):
                        args.append(self.Expression())
                    self.Consume(')')
                pfe = FunctionCall(pfe, args, pfe.loc)
            else:
                raise Exception()
        return pfe

    def PrimaryExpression(self):
        if self.hasConsumed('('):
            e = self.Expression()
            self.Consume(')')
            return e
        elif self.Peak == 'NUMBER':
            val = self.Consume('NUMBER')
            return Literal(val.val, val.loc)
        elif self.Peak == 'REAL':
            val = self.Consume('REAL')
            return Literal(val.val, val.loc)
        elif self.Peak == 'true':
            val = self.Consume('true')
            return Literal(True, val.loc)
        elif self.Peak == 'false':
            val = self.Consume('false')
            return Literal(False, val.loc)
        elif self.Peak == 'STRING':
            val = self.Consume('STRING')
            return Literal(val.val, val.loc)
        elif self.Peak == 'ID':
            return self.parseDesignator()
        self.Error('Expected NUM, ID or (expr), got {0}'.format(self.Peak))
