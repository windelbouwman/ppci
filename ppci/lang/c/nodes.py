"""
    Contains classes for the abstract syntax tree (AST) nodes for the C
    language.
"""

from ...common import SourceLocation


class CompilationUnit:
    """ A single compilation unit """
    def __init__(self, declarations):
        self.decls = declarations

    def __repr__(self):
        return 'Compilation unit with {} declarations'.format(len(self.decls))


class DeclSpec:
    """ Contains a type and a set of modifiers """
    def __init__(self):
        self.typ = None
        self.modifiers = []

    @property
    def has_type(self):
        return self.typ is not None

    def __repr__(self):
        return '[decl-spec typ={} mod={}]'.format(self.typ, self.modifiers)


class Declaration:
    """ A single declaration """
    def __init__(self):
        self.typ = None
        self.modifiers = []
        self.name = None
        self.f = False

    @property
    def is_function(self):
        return self.f

    def __repr__(self):
        return '[decl typ={} name={}]'.format(self.typ, self.name)


class FunctionDeclaration(Declaration):
    pass


# A type system:
class CType:
    """ Base class for all types """
    @property
    def is_void(self):
        return isinstance(self, VoidType)


class VoidType(CType):
    pass


class FunctionType(CType):
    def __init__(self, arg_types, return_type):
        self.arg_types = arg_types
        self.return_type = return_type


class ArrayType(CType):
    """ Array type """
    pass


class StructType(CType):
    """ Structure type """
    pass


class NamedType(CType):
    def __init__(self, name):
        self.name = name


class IntegerType(NamedType):
    pass


class FloatingPointType(NamedType):
    pass


# Statements:
class Statement:
    def __init__(self, loc):
        self.loc = loc


class Compound(Statement):
    def __init__(self, statements, loc):
        super().__init__(loc)
        self.statements = statements


class If(Statement):
    """ If statement """
    def __init__(self, condition, yes, no, loc):
        super().__init__(loc)
        self.condition = condition
        self.yes = yes
        self.no = no


class Switch:
    """ Switch statement """
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class While(Statement):
    """ While statement """
    def __init__(self, condition, body, loc):
        super().__init__(loc)
        self.condition = condition
        self.body = body


class DoWhile(Statement):
    """ Do-while statement """
    def __init__(self, body, condition, loc):
        super().__init__(loc)
        self.condition = condition
        self.body = body


class For(Statement):
    """ For statement """
    def __init__(self, condition, body, loc):
        super().__init__(loc)
        self.condition = condition
        self.body = body


class Break(Statement):
    """ Break statement """
    pass


class Case:
    """ Case statement """
    def __init__(self, value):
        self.value = value


class Goto(Statement):
    """ Goto statement """
    pass


class Return(Statement):
    """ Return statement """
    def __init__(self, value, loc):
        super().__init__(loc)
        self.value = value


class FunctionCall:
    """ Function call """
    def __init__(self, name, args):
        self.name = name
        self.args = args


class Expression:
    """ Some nice common base class for expressions """
    def __init__(self, loc: SourceLocation):
        self.loc = loc


class Binop(Expression):
    """ Binary operator """
    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return '({} {} {})'.format(self.a, self.op, self.b)


class VariableAccess(Expression):
    def __init__(self, name, loc):
        super().__init__(loc)
        self.name = name

    def __repr__(self):
        return '[ACCESS {}]'.format(self.name)


class Constant(Expression):
    def __init__(self, value, loc):
        super().__init__(loc)
        self.value = value

    def __repr__(self):
        return '[CONST {}]'.format(self.value)
