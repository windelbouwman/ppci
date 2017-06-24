""" A context where other parts share global state """

from .types import BareType
from . import types


def type_tuple(*args):
    return tuple(sorted(args))


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, march):
        self.coptions = coptions
        self.march = march

        self.atomic_types = {
            type_tuple('void'): BareType.VOID,
            type_tuple('char',): BareType.CHAR,
            type_tuple('signed', 'char'): BareType.SCHAR,
            type_tuple('unsigned', 'char'): BareType.UCHAR,
            type_tuple('short',): BareType.SHORT,
            type_tuple('short', 'int'): BareType.SHORT,
            type_tuple('signed', 'short', 'int'): BareType.SHORT,
            type_tuple('unsigned', 'short'): BareType.USHORT,
            type_tuple('unsigned', 'short', 'int'): BareType.USHORT,
            type_tuple('int',): BareType.INT,
            type_tuple('signed', 'int',): BareType.INT,
            type_tuple('unsigned', 'int',): BareType.UINT,
            type_tuple('unsigned',): BareType.UINT,
            type_tuple('long',): BareType.LONG,
            type_tuple('long', 'int'): BareType.LONG,
            type_tuple('unsigned', 'long'): BareType.ULONG,
            type_tuple('unsigned', 'long', 'int'): BareType.ULONG,
            type_tuple('long', 'long',): BareType.LONGLONG,
            type_tuple('long', 'long', 'int'): BareType.LONGLONG,
            type_tuple('signed', 'long', 'long', 'int'):
                BareType.LONGLONG,
            type_tuple('unsigned', 'long', 'long'): BareType.ULONGLONG,
            type_tuple('unsigned', 'long', 'long', 'int'):
                BareType.ULONGLONG,
            type_tuple('float',): BareType.FLOAT,
            type_tuple('double',): BareType.DOUBLE,
            type_tuple('long', 'double'): BareType.LONGDOUBLE,
        }

        int_size = self.march.byte_sizes['int']
        self.type_size_map = {
            BareType.CHAR: 1,
            BareType.SCHAR: 1,
            BareType.UCHAR: 1,
            BareType.SHORT: 2,
            BareType.USHORT: 2,
            BareType.INT: int_size,
            BareType.UINT: int_size,
            BareType.LONG: 8,
            BareType.ULONG: 8,
            BareType.FLOAT: 4,
            BareType.DOUBLE: 8,
        }

    def is_valid(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        a = self.atomic_types[key]
        return BareType(a)

    def equal_types(self, typ1, typ2):
        """ Check for type equality """
        # TODO: enhance!
        if typ1 is typ2:
            # A short circuit:
            return True
        # elif isinstance(typ1, nodes.QualifiedType):
        #    # Handle qualified types:
        #    if isinstance(typ2, nodes.QualifiedType):
        #        return typ1.qualifiers == typ2.qualifiers and \
        #            self.equal_types(typ1.typ, typ2.typ)
        #    else:
        #        return (not typ1.qualifiers) and \
        #            self.equal_types(typ1.typ, typ2)
        # elif isinstance(typ2, nodes.QualifiedType):
        #    # Handle qualified types (we know that typ1 unqualified)
        #    return (not typ2.qualifiers) and self.equal_types(typ1, typ2.typ)
        elif isinstance(typ1, types.BareType):
            if isinstance(typ2, types.BareType):
                return typ1.type_id == typ2.type_id
        elif isinstance(typ1, types.IdentifierType):
            if isinstance(typ2, types.IdentifierType):
                return typ1.name == typ2.name
        elif isinstance(typ1, types.FunctionType):
            if isinstance(typ2, types.FunctionType):
                return len(typ1.arg_types) == len(typ2.arg_types) and \
                    self.equal_types(typ1.return_type, typ2.return_type) and \
                    all(self.equal_types(a1, a2) for a1, a2 in zip(
                        typ1.arg_types, typ2.arg_types))
        elif isinstance(typ1, types.PointerType):
            if isinstance(typ2, types.PointerType):
                return self.equal_types(typ1.element_type, typ2.element_type)
        elif isinstance(typ1, types.UnionType):
            if isinstance(typ2, types.UnionType):
                return typ1 is typ2
        elif isinstance(typ1, types.StructType):
            if isinstance(typ2, types.StructType):
                return typ1 is typ2
        elif isinstance(typ1, types.EnumType):
            if isinstance(typ2, types.EnumType):
                return typ1 is typ2
        else:
            raise NotImplementedError(str(typ1))
        return False

    def resolve_type(self, typ: types.IdentifierType):
        """ Given a type, look behind the identifiertype """
        if isinstance(typ, types.IdentifierType):
            return typ.typ
        else:
            return typ

    def sizeof(self, typ: types.CType):
        """ Given a type, determine its size in whole bytes """
        assert isinstance(typ, types.CType)
        if isinstance(typ, types.ArrayType):
            element_size = self.sizeof(typ.element_type)
            if typ.size is None:
                self.error('Size of array could not be determined!', typ)
            assert isinstance(typ.size, int)
            array_size = typ.size
            return element_size * array_size
        elif isinstance(typ, types.BareType):
            return self.type_size_map[typ.type_id]
        elif isinstance(typ, types.IdentifierType):  # TODO: is this needed?
            return self.sizeof(self.resolve_type(typ))
        elif isinstance(typ, types.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            # TODO: round up somewhat?
            return sum(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, types.UnionType):
            if not typ.complete:
                self.error('Type is incomplete, size unknown', typ)
            return max(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, types.EnumType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            # For enums take int as the type
            return self.march.byte_sizes['int']
        elif isinstance(typ, types.PointerType):
            return self.march.byte_sizes['ptr']
        elif isinstance(typ, types.FunctionType):
            # TODO: can we determine size of a function type? Should it not
            # be pointer to a function?
            return self.march.byte_sizes['ptr']
        elif isinstance(typ, types.QualifiedType):
            return self.sizeof(typ.typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
