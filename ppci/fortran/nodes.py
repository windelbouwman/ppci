"""
    Contains fortran langauge AST (abstract syntax tree) nodes.
"""


class Node:
    def __init__(self, loc):
        self.loc = loc


class Program(Node):
    """ A fortran program """
    def __init__(self, name, variables, statements, loc):
        super().__init__(loc)
        self.name = name
        self.variables = variables
        self.statements = statements

    def __repr__(self):
        return 'PROGRAM {}'.format(self.name)


class Variable(Node):
    def __init__(self, typ, name, loc):
        super().__init__(loc)
        self.typ = typ
        self.name = name

    def __repr__(self):
        return 'VAR {} {}'.format(self.typ, self.name)


class Statement(Node):
    """ A single fortran statement """
    pass


class Assignment(Statement):
    def __init__(self, var, expr, loc):
        super().__init__(loc)
        self.var = var
        self.expr = expr

    def __repr__(self):
        return '{} = {}'.format(self.var, self.expr)


class Continue(Statement):
    """ Continue statement """
    def __repr__(self):
        return 'CONTINUE'


class Data(Statement):
    """ Data statement """
    def __init__(self, nlist, clist, loc):
        super().__init__(loc)
        self.nlist = nlist
        self.clist = clist

    def __repr__(self):
        return 'Data {} = {}'.format(self.nlist, self.clist)


class Format(Statement):
    """ Format statement """
    def __repr__(self):
        return 'FORMAT (...)'


class GoTo(Statement):
    def __init__(self, x, loc):
        super().__init__(loc)
        self.x = x

    def __repr__(self):
        return 'GO TO {}'.format(self.x)


class IfArith(Statement):
    """ Arithmatic if """
    def __init__(self, expr, s1, s2, s3, loc):
        super().__init__(loc)
        self.expr = expr
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def __repr__(self):
        return 'IF (a,b,c)'


class Print(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'PRINT {}, {}'.format(self.fmt, args2)


class Read(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'READ {}, {}'.format(self.fmt, args2)


class Stop(Statement):
    """ Stop statement """
    def __init__(self, msg, loc):
        super().__init__(loc)
        self.msg = msg

    def __repr__(self):
        return 'STOP'


class Write(Statement):
    def __init__(self, fmt, args, loc):
        super().__init__(loc)
        self.fmt = fmt
        self.args = args

    def __repr__(self):
        args2 = ', '.join(map(str, self.args))
        return 'WRITE {}, {}'.format(self.fmt, args2)


class For(Statement):
    pass


class Expression(Node):
    pass


class Binop(Expression):
    """ Binary operation """
    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return '({} {} {})'.format(self.a, self.op, self.b)


class Unop(Expression):
    def __init__(self, op, a, loc):
        super().__init__(loc)
        self.op = op
        self.a = a

    def __repr__(self):
        return '({} {})'.format(self.op, self.a)


class VarRef(Expression):
    def __init__(self, vname, loc):
        super().__init__(loc)
        self.vname = vname

    def __repr__(self):
        return self.vname


class Const(Expression):
    def __init__(self, val, typ, loc):
        super().__init__(loc)
        self.val = val
        self.typ = typ

    def __repr__(self):
        return '{}<{}>'.format(self.typ, self.val)
