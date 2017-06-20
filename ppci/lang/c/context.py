""" A context where other parts share global state """

from .types import BareType


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

    def is_valid(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        a = self.atomic_types[key]
        return BareType(a)
