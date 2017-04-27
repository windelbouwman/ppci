"""
    Contains classes for the abstract syntax tree (AST) nodes for the C
    language.
"""

from ...common import SourceLocation


class CompilationUnit:
    """ A single compilation unit """
    def __init__(self, declarations):
        self.declarations = declarations

    def __repr__(self):
        return 'Compilation unit with {} declarations'.format(
            len(self.declarations))


class DeclSpec:
    """ Contains a type and a set of modifiers """
    def __init__(self):
        self.typ = None
        self.storage_class = None
        self.type_specifiers = []
        self.type_qualifiers = set()

    def __repr__(self):
        return '[decl-spec mod={}]'.format(self.storage_class)


class Declaration:
    def __init__(self, typ, loc):
        self.typ = typ
        self.loc = loc

    @property
    def is_function(self):
        return isinstance(self, FunctionDeclaration)


class NamedDeclaration(Declaration):
    """ A single declaration """
    def __init__(self, typ, name, loc):
        super().__init__(typ, loc)
        self.storage_class = None
        self.name = name


class VariableDeclaration(NamedDeclaration):
    def __init__(self, typ, name, initial_value, loc):
        super().__init__(typ, name, loc)
        self.initial_value = initial_value

    def __repr__(self):
        return 'Variable [decl typ={} name={}, {}]'.format(
            self.typ, self.name, self.storage_class)


class ParameterDeclaration(Declaration):
    pass


class FunctionDeclaration(NamedDeclaration):
    def __init__(self, typ, name, loc):
        super().__init__(typ, name, loc)
        self.body = None

    def __repr__(self):
        return 'FunctionDeclaration typ={} name={}'.format(
            self.typ, self.name)


# A type system:
class CType:
    """ Base class for all types """
    def __init__(self):
        self.qualifiers = set()

    @property
    def is_void(self):
        if isinstance(self, IdentifierType):
            return 'void' in self.names
        else:
            return False


# class SimpleType(CType):
#     pass


class FunctionType(CType):
    def __init__(self, arg_types, return_type):
        super().__init__()
        self.arg_types = arg_types
        self.return_type = return_type

    def __repr__(self):
        return 'Function-type'


class ArrayType(CType):
    """ Array type """
    def __init__(self, element_type):
        super().__init__()
        self.element_type = element_type

    def __repr__(self):
        return 'Array-type'


class StructType(CType):
    """ Structure type """
    def __init__(self, name, loc):
        super().__init__()
        self.name = name

    def __repr__(self):
        return 'Structured-type'


class PointerType(CType):
    """ The famous pointer! """
    def __init__(self, pointed_type):
        super().__init__()
        self.pointed_type = pointed_type

    def __repr__(self):
        return 'Pointer-type'


class IdentifierType(CType):
    def __init__(self, names):
        super().__init__()
        self.names = names

    def __repr__(self):
        return 'IdentifierType: {}'.format(self.names)


# class VoidType(NamedType):
#    """ Type representing no value """
#    def __init__(self):
#        super().__init__('void')


# class IntegerType(NamedType):
#    pass


# class FloatingPointType(NamedType):
#    pass


# Statements:
class Statement:
    def __init__(self, loc):
        self.loc = loc


class Compound(Statement):
    def __init__(self, statements, loc):
        super().__init__(loc)
        self.statements = statements

    def __repr__(self):
        return 'Compound'


class If(Statement):
    """ If statement """
    def __init__(self, condition, yes, no, loc):
        super().__init__(loc)
        self.condition = condition
        self.yes = yes
        self.no = no

    def __repr__(self):
        return 'If'


class Switch(Statement):
    """ Switch statement """
    def __init__(self, condition, body, loc):
        super().__init__(loc)
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

    def __repr__(self):
        return 'Do-while'


class For(Statement):
    """ For statement """
    def __init__(self, init, condition, post, body, loc):
        super().__init__(loc)
        self.init = init
        self.condition = condition
        self.post = post
        self.body = body

    def __repr__(self):
        return 'For'


class Break(Statement):
    """ Break statement """
    def __repr__(self):
        return 'Break'


class Case:
    """ Case statement """
    def __init__(self, value, loc):
        # super().__init__(loc)
        self.value = value

    def __repr__(self):
        return 'Case'


class Goto(Statement):
    """ Goto statement """
    def __init__(self, label, loc):
        super().__init__(loc)

    def __repr__(self):
        return 'Goto'


class Return(Statement):
    """ Return statement """
    def __init__(self, value, loc):
        super().__init__(loc)
        self.value = value

    def __repr__(self):
        return 'Return'


class Empty(Statement):
    """ Do nothing! """
    pass


class Expression:
    """ Some nice common base class for expressions """
    def __init__(self, loc: SourceLocation):
        self.loc = loc


class FunctionCall(Expression):
    """ Function call """
    def __init__(self, name, args, loc):
        super().__init__(loc)
        self.name = name
        self.args = args

    def __repr__(self):
        return 'FunctionCall {}'.format(self.name)


class Binop(Expression):
    """ Binary operator """
    def __init__(self, a, op, b, loc):
        super().__init__(loc)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return 'BinaryOp {}'.format(self.op)


class Unop(Expression):
    """ Unary operator """
    def __init__(self, op, a, loc):
        super().__init__(loc)
        self.a = a
        self.op = op

    def __repr__(self):
        return 'UnaryOp {}'.format(self.op)


class Cast(Expression):
    def __init__(self, to_typ, expr, loc):
        super().__init__(loc)
        self.to_typ = to_typ
        self.expr = expr

    def __repr__(self):
        return 'Cast {}'.format(self.to_typ)


class Sizeof(Expression):
    def __init__(self, sizeof_typ, loc):
        super().__init__(loc)
        self.sizeof_typ = sizeof_typ

    def __repr__(self):
        return 'Sizeof {}'.format(self.sizeof_typ)


class VariableAccess(Expression):
    def __init__(self, name, loc):
        super().__init__(loc)
        self.name = name

    def __repr__(self):
        return 'Id {}'.format(self.name)


class Constant(Expression):
    def __init__(self, value, loc):
        super().__init__(loc)
        self.value = value

    def __repr__(self):
        return 'Const {}'.format(self.value)
