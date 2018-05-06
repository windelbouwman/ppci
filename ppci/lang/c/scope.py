""" C scoping functions """
from .nodes.declarations import CDeclaration
from .nodes.types import BasicType
from .nodes import types, expressions, declarations


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

    def equal_types(self, typ1: types.CType, typ2, unqualified=False):
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
        elif isinstance(typ1, BasicType):
            if isinstance(typ2, BasicType):
                return typ1.type_id == typ2.type_id
        elif isinstance(typ1, types.FunctionType):
            if isinstance(typ2, types.FunctionType):
                return \
                    len(typ1.argument_types) == len(typ2.argument_types) and \
                    self.equal_types(typ1.return_type, typ2.return_type) and \
                    all(self.equal_types(a1, a2) for a1, a2 in zip(
                        typ1.argument_types, typ2.argument_types))
        elif isinstance(typ1, types.IndexableType):
            if isinstance(typ2, types.IndexableType):
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

    def is_const_expr(self, expr):
        """ Test if an expression can be evaluated at compile time """
        if isinstance(expr, expressions.BinaryOperator):
            return self.is_const_expr(expr.a) and self.is_const_expr(expr.b)
        elif isinstance(expr, expressions.NumericLiteral):
            return True
        elif isinstance(expr, expressions.CharLiteral):
            return True
        elif isinstance(expr, expressions.Sizeof):
            return True
        elif isinstance(expr, declarations.EnumConstantDeclaration):
            return True
        elif isinstance(expr, expressions.Cast):
            return self.is_const_expr(expr.expr)
        elif isinstance(expr, expressions.VariableAccess):
            return self.is_const_expr(expr.variable)
        else:
            return False


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

    def insert(self, declaration: CDeclaration):
        """ Insert a variable into the current scope """
        assert isinstance(declaration, CDeclaration)
        assert declaration.name not in self.var_map
        self.var_map[declaration.name] = declaration

    def update(self, declaration: CDeclaration):
        """ Update an existing name to a new declaration """
        assert isinstance(declaration, CDeclaration)
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
