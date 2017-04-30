""" A context where other parts share global state """

from . import nodes


class CContext:
    """ A context as a substitute for global data """
    def __init__(self, coptions, march):
        self.coptions = coptions
        self.march = march

        self.atomic_types = {
            ('void',): nodes.BareType.VOID,
            ('char',): nodes.BareType.CHAR,
            ('signed', 'char'): nodes.BareType.SCHAR,
            ('unsigned', 'char'): nodes.BareType.UCHAR,
            ('short',): nodes.BareType.SHORT,
            ('short', 'int'): nodes.BareType.SHORT,
            ('unsigned', 'short'): nodes.BareType.USHORT,
            ('unsigned', 'short', 'int'): nodes.BareType.USHORT,
            ('int',): nodes.BareType.INT,
            ('signed', 'int',): nodes.BareType.INT,
            ('unsigned', 'int',): nodes.BareType.UINT,
            ('unsigned',): nodes.BareType.UINT,
            ('long',): nodes.BareType.LONG,
            ('long', 'int'): nodes.BareType.LONG,
            ('unsigned', 'long'): nodes.BareType.ULONG,
            ('unsigned', 'long', 'int'): nodes.BareType.ULONG,
            ('long', 'long',): nodes.BareType.LONGLONG,
            ('unsigned', 'long', 'long'): nodes.BareType.ULONGLONG,
            ('float',): nodes.BareType.FLOAT,
            ('double',): nodes.BareType.DOUBLE,
            ('long', 'double'): nodes.BareType.LONGDOUBLE,
        }

    def is_valid(self, type_specifiers):
        key = tuple(type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        key = tuple(type_specifiers)
        a = self.atomic_types[key]
        return nodes.BareType(a)
