""" This module contains internal representations of types. """


# A type system:
class CType:
    """ Base class for all types """
    @property
    def is_void(self):
        return isinstance(self, BareType) and self.type_id == BareType.VOID


# TODO: maybe merge qualifiers into a type itself?
class QualifiedType(CType):
    """ A qualified type """
    def __init__(self, qualifiers, typ):
        self.qualifiers = qualifiers
        assert isinstance(typ, CType)
        self.typ = typ

    def __repr__(self):
        return 'Qualified type'


class FunctionType(CType):
    """ Function type """
    def __init__(self, argument_types, return_type):
        super().__init__()
        # self.arguments = arguments
        # assert all(isinstance(a, VariableDeclaration) for a in arguments)
        self.argument_types = argument_types
        assert all(isinstance(t, CType) for t in self.argument_types)
        self.return_type = return_type
        assert isinstance(return_type, CType)

    def __repr__(self):
        return 'Function-type'


class IndexableType(CType):
    """ Array or pointer type """
    def __init__(self, element_type):
        super().__init__()
        assert isinstance(element_type, CType)
        self.element_type = element_type


class ArrayType(IndexableType):
    """ Array type """
    def __init__(self, element_type, size):
        super().__init__(element_type)
        self.size = size

    def __repr__(self):
        return 'Array-type'


class PointerType(IndexableType):
    """ The famous pointer! """
    def __repr__(self):
        return 'Pointer-type'


class EnumType(CType):
    """ Enum type """
    def __init__(self, values=None):
        super().__init__()
        self.values = values

    @property
    def complete(self):
        return self.values is not None

    def __repr__(self):
        return 'Enum-type'


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

    def has_field(self, name: str):
        return name in self.field_map

    def get_field(self, name: str):
        assert isinstance(name, str)
        return self.field_map[name]


class StructType(StructOrUnionType):
    """ Structure type """
    def __repr__(self):
        return 'Structured-type'


class Field:
    """ A field inside a union or struct """
    def __init__(self, typ, name, offset, bitsize):
        self.typ = typ
        assert isinstance(typ, CType)
        self.name = name
        self.bitsize = bitsize
        self.offset = offset


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


class IdentifierType(CType):
    """ Refering to a typedef type """
    def __init__(self, name, typ):
        super().__init__()
        self.name = name
        self.typ = typ

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
        return 'Native type {}'.format(self.type_id)


# class VoidType(NamedType):
#    """ Type representing no value """
#    def __init__(self):
#        super().__init__('void')


# class IntegerType(NamedType):
#    pass


# class FloatingPointType(NamedType):
#    pass
