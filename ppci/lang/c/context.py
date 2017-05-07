""" A context where other parts share global state """

from . import nodes


def type_tuple(*args):
    return tuple(sorted(args))


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, march):
        self.coptions = coptions
        self.march = march

        self.atomic_types = {
            type_tuple('void'): nodes.BareType.VOID,
            type_tuple('char',): nodes.BareType.CHAR,
            type_tuple('signed', 'char'): nodes.BareType.SCHAR,
            type_tuple('unsigned', 'char'): nodes.BareType.UCHAR,
            type_tuple('short',): nodes.BareType.SHORT,
            type_tuple('short', 'int'): nodes.BareType.SHORT,
            type_tuple('signed', 'short', 'int'): nodes.BareType.SHORT,
            type_tuple('unsigned', 'short'): nodes.BareType.USHORT,
            type_tuple('unsigned', 'short', 'int'): nodes.BareType.USHORT,
            type_tuple('int',): nodes.BareType.INT,
            type_tuple('signed', 'int',): nodes.BareType.INT,
            type_tuple('unsigned', 'int',): nodes.BareType.UINT,
            type_tuple('unsigned',): nodes.BareType.UINT,
            type_tuple('long',): nodes.BareType.LONG,
            type_tuple('long', 'int'): nodes.BareType.LONG,
            type_tuple('unsigned', 'long'): nodes.BareType.ULONG,
            type_tuple('unsigned', 'long', 'int'): nodes.BareType.ULONG,
            type_tuple('long', 'long',): nodes.BareType.LONGLONG,
            type_tuple('long', 'long', 'int'): nodes.BareType.LONGLONG,
            type_tuple('signed', 'long', 'long', 'int'):
                nodes.BareType.LONGLONG,
            type_tuple('unsigned', 'long', 'long'): nodes.BareType.ULONGLONG,
            type_tuple('unsigned', 'long', 'long', 'int'):
                nodes.BareType.ULONGLONG,
            type_tuple('float',): nodes.BareType.FLOAT,
            type_tuple('double',): nodes.BareType.DOUBLE,
            type_tuple('long', 'double'): nodes.BareType.LONGDOUBLE,
        }

    def is_valid(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        key = type_tuple(*type_specifiers)
        a = self.atomic_types[key]
        return nodes.BareType(a)
