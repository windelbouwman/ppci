""" C scoping functions """
from .nodes.declarations import Declaration
from .nodes.types import BasicType


def type_tuple(*args):
    """ Return sorted tuple """
    return tuple(sorted(args))


class RootScope:
    """ Root scope with basic types """
    def __init__(self):
        self.atomic_types = {
            type_tuple('void'): BasicType.VOID,
            type_tuple('char',): BasicType.CHAR,
            type_tuple('signed', 'char'): BasicType.CHAR,
            type_tuple('unsigned', 'char'): BasicType.UCHAR,
            type_tuple('short',): BasicType.SHORT,
            type_tuple('signed', 'short',): BasicType.SHORT,
            type_tuple('short', 'int'): BasicType.SHORT,
            type_tuple('signed', 'short', 'int'): BasicType.SHORT,
            type_tuple('unsigned', 'short'): BasicType.USHORT,
            type_tuple('unsigned', 'short', 'int'): BasicType.USHORT,
            type_tuple('int',): BasicType.INT,
            type_tuple('signed', 'int',): BasicType.INT,
            type_tuple('unsigned', 'int',): BasicType.UINT,
            type_tuple('unsigned',): BasicType.UINT,
            type_tuple('long',): BasicType.LONG,
            type_tuple('signed', 'long',): BasicType.LONG,
            type_tuple('long', 'int'): BasicType.LONG,
            type_tuple('signed', 'long', 'int'): BasicType.LONG,
            type_tuple('unsigned', 'long'): BasicType.ULONG,
            type_tuple('unsigned', 'long', 'int'): BasicType.ULONG,
            type_tuple('long', 'long',): BasicType.LONGLONG,
            type_tuple('signed', 'long', 'long',): BasicType.LONGLONG,
            type_tuple('long', 'long', 'int'): BasicType.LONGLONG,
            type_tuple('signed', 'long', 'long', 'int'):
                BasicType.LONGLONG,
            type_tuple('unsigned', 'long', 'long'): BasicType.ULONGLONG,
            type_tuple('unsigned', 'long', 'long', 'int'):
                BasicType.ULONGLONG,
            type_tuple('float',): BasicType.FLOAT,
            type_tuple('double',): BasicType.DOUBLE,
            type_tuple('long', 'double'): BasicType.LONGDOUBLE,
        }

    def is_valid(self, type_specifiers):
        """ Check if the type specifiers refer to a valid basic type """
        assert isinstance(type_specifiers, (list, tuple))
        key = type_tuple(*type_specifiers)
        return key in self.atomic_types

    def get_type(self, type_specifiers):
        """ Create a new instance for the given type specifiers """
        assert isinstance(type_specifiers, (list, tuple))
        key = type_tuple(*type_specifiers)
        a = self.atomic_types[key]
        return BasicType(a)


class Scope:
    """ A variable scope """
    def __init__(self, parent=None):
        self.parent = parent
        # Different namespaces in this scope:
        self.var_map = {}
        self.tags = {}
        self.labels = {}

    def is_defined(self, name, all_scopes=True):
        """ Check if the name is defined """
        if name in self.var_map:
            return True
        elif self.parent and all_scopes:
            return self.parent.is_defined(name)
        else:
            return False

    def insert(self, declaration: Declaration):
        """ Insert a variable into the current scope """
        assert isinstance(declaration, Declaration)
        assert declaration.name not in self.var_map
        self.var_map[declaration.name] = declaration

    def update(self, declaration: Declaration):
        """ Update an existing name to a new declaration """
        assert isinstance(declaration, Declaration)
        assert declaration.name in self.var_map
        self.var_map[declaration.name] = declaration

    def has_tag(self, name):
        if self.parent:
            # TODO: make tags a flat space?
            return self.parent.has_tag(name)
        return name in self.tags

    def get_tag(self, name):
        """ Get a struct by tag """
        if self.parent:
            return self.parent.get_tag(name)
        return self.tags[name]

    def add_tag(self, name, o):
        if self.parent:
            return self.parent.add_tag(name, o)
        self.tags[name] = o

    def get(self, name):
        """ Get the symbol with the given name """
        if name in self.var_map:
            return self.var_map[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise KeyError(name)
