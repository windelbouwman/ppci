""" Classes for the abstract syntax tree (AST) nodes for the C language.
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
        # self.type_specifiers = []
        # self.type_qualifiers = set()

    def __repr__(self):
        return '[decl-spec mod={}]'.format(self.storage_class)


class Declaration:
    def __init__(self, typ, loc):
        assert isinstance(typ, CType)
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


class Typedef(NamedDeclaration):
    """ Type definition """
    def __repr__(self):
        return 'Typedef {}'.format(self.name)


class VariableDeclaration(NamedDeclaration):
    def __init__(self, typ, name, initial_value, loc):
        super().__init__(typ, name, loc)
        self.initial_value = initial_value

    def __repr__(self):
        return 'Variable [decl typ={} name={}, {}]'.format(
            self.typ, self.name, self.storage_class)


class ConstantDeclaration(NamedDeclaration):
    def __init__(self, typ, name, value, loc):
        super().__init__(typ, name, loc)
        self.value = value

    def __repr__(self):
        return 'Const [typ={} name={}, {}]'.format(
            self.typ, self.name, self.value)


class ParameterDeclaration(Declaration):
    pass


class FunctionDeclaration(NamedDeclaration):
    """ A function declaration """
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
        return isinstance(self, BareType) and self.type_id == BareType.VOID


class QualifiedType(CType):
    """ A qualified type """
    def __init__(self, qualifiers, typ):
        self.qualifiers = qualifiers
        self.typ = typ

    def __repr__(self):
        return 'Qualified type'


class FunctionType(CType):
    def __init__(self, arguments, return_type):
        super().__init__()
        self.arguments = arguments
        assert all(isinstance(a, VariableDeclaration) for a in arguments)
        self.arg_types = [a.typ for a in arguments]
        self.return_type = return_type

    def __repr__(self):
        return 'Function-type'


class ArrayType(CType):
    """ Array type """
    def __init__(self, element_type, size):
        super().__init__()
        self.element_type = element_type
        self.size = size

    def __repr__(self):
        return 'Array-type'


class EnumType(CType):
    """ Enum type """
    def __init__(self, values=None):
        super().__init__()
        self.values = values

    @property
    def complete(self):
        return self.values is not None


class StructOrUnionType(CType):
    """ Common base for struct and union types """
    def __init__(self, tag=None, fields=None):
        super().__init__()
        self._fields = None
        self.tag = tag
        self.fields = fields

    @property
    def incomplete(self):
        """ Check whether this type is incomplete or not """
        return self.fields is None

    @property
    def complete(self):
        return not self.incomplete

    def get_fields(self):
        return self._fields

    def set_fields(self, fields):
        self._fields = fields
        if fields:
            self.field_map = {f.name: f for f in fields}

    fields = property(get_fields, set_fields)

    def has_field(self, name):
        return name in self.field_map

    def get_field(self, name):
        return self.field_map[name]


class StructType(StructOrUnionType):
    """ Structure type """
    def __repr__(self):
        return 'Structured-type'


# class StructReferenceType(CType):
#    """ Refering to a tagged struct """
#    def __init__(self, name):
#        super().__init__()
#        self.name = name
#
#    def __repr__(self):
#        return 'IdentifierType: {}'.format(self.name)


class UnionType(StructOrUnionType):
    """ Union type """
    def __repr__(self):
        return 'Union-type'


class PointerType(CType):
    """ The famous pointer! """
    def __init__(self, pointed_type):
        super().__init__()
        self.pointed_type = pointed_type

    def __repr__(self):
        return 'Pointer-type'


class IdentifierType(CType):
    """ Refering to a typedef type """
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return 'IdentifierType: {}'.format(self.name)


class BareType(CType):
    """ This type is one of: int, unsigned int, float or void """
    VOID = 'void'
    CHAR = 'char'
    SCHAR = 'signed char'
    UCHAR = 'unsigned char'
    SHORT = 'short'
    USHORT = 'unsigned short'
    INT = 'int'
    UINT = 'unsigned int'
    LONG = 'long'
    ULONG = 'unsigned long'
    LONGLONG = 'long long'
    ULONGLONG = 'unsigned long long'
    FLOAT = 'float'
    DOUBLE = 'double'
    LONGDOUBLE = 'long double'

    def __init__(self, type_id):
        super().__init__()
        self.type_id = type_id

    def __repr__(self):
        return 'Basetype {}'.format(self.type_id)


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
    def __repr__(self):
        return 'Empty'


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
        assert isinstance(a, Expression)
        assert isinstance(b, Expression)
        self.a = a
        self.op = op
        self.b = b

    def __repr__(self):
        return 'BinaryOp {}'.format(self.op)


class Unop(Expression):
    """ Unary operator """
    def __init__(self, op, a, loc):
        super().__init__(loc)
        assert isinstance(a, Expression)
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
    """ Sizeof operator """
    def __init__(self, sizeof_typ, loc):
        super().__init__(loc)
        self.sizeof_typ = sizeof_typ

    def __repr__(self):
        return 'Sizeof {}'.format(self.sizeof_typ)


class ArrayIndex(Expression):
    """ Array indexing """
    def __init__(self, base, index, loc):
        super().__init__(loc)
        self.base = base
        self.index = index

    def __repr__(self):
        return 'Array index'


class FieldSelect(Expression):
    """ Select a field in a struct """
    def __init__(self, base, field, loc):
        super().__init__(loc)
        self.base = base
        self.field = field

    def __repr__(self):
        return 'Field select'


class VariableAccess(Expression):
    def __init__(self, name, loc):
        super().__init__(loc)
        self.name = name

    def __repr__(self):
        return 'Id {}'.format(self.name)


class Literal(Expression):
    def __init__(self, value, loc):
        super().__init__(loc)
        self.value = value

    def __repr__(self):
        return 'Literal {}'.format(self.value)
