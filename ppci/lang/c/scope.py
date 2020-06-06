""" C scoping functions """
from .nodes.types import BasicType
from .nodes import types, expressions, declarations
from ...utils.collections import OrderedDict


def type_tuple(*args):
    """ Return sorted tuple """
    return tuple(sorted(args))


class RootScope:
    """ Root scope with basic types """

    def __init__(self):
        self.atomic_types = {
            type_tuple("void"): BasicType.VOID,
            type_tuple("char"): BasicType.CHAR,
            type_tuple("signed", "char"): BasicType.CHAR,
            type_tuple("unsigned", "char"): BasicType.UCHAR,
            type_tuple("short"): BasicType.SHORT,
            type_tuple("signed", "short"): BasicType.SHORT,
            type_tuple("short", "int"): BasicType.SHORT,
            type_tuple("signed", "short", "int"): BasicType.SHORT,
            type_tuple("unsigned", "short"): BasicType.USHORT,
            type_tuple("unsigned", "short", "int"): BasicType.USHORT,
            type_tuple("int"): BasicType.INT,
            type_tuple("signed"): BasicType.INT,
            type_tuple("signed", "int"): BasicType.INT,
            type_tuple("unsigned", "int"): BasicType.UINT,
            type_tuple("unsigned"): BasicType.UINT,
            type_tuple("long"): BasicType.LONG,
            type_tuple("signed", "long"): BasicType.LONG,
            type_tuple("long", "int"): BasicType.LONG,
            type_tuple("signed", "long", "int"): BasicType.LONG,
            type_tuple("unsigned", "long"): BasicType.ULONG,
            type_tuple("unsigned", "long", "int"): BasicType.ULONG,
            type_tuple("long", "long"): BasicType.LONGLONG,
            type_tuple("signed", "long", "long"): BasicType.LONGLONG,
            type_tuple("long", "long", "int"): BasicType.LONGLONG,
            type_tuple("signed", "long", "long", "int"): BasicType.LONGLONG,
            type_tuple("unsigned", "long", "long"): BasicType.ULONGLONG,
            type_tuple("unsigned", "long", "long", "int"): BasicType.ULONGLONG,
            type_tuple("float"): BasicType.FLOAT,
            type_tuple("double"): BasicType.DOUBLE,
            type_tuple("long", "double"): BasicType.LONGDOUBLE,
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
                return (
                    len(typ1.argument_types) == len(typ2.argument_types)
                    and self.equal_types(typ1.return_type, typ2.return_type)
                    and all(
                        self.equal_types(a1, a2)
                        for a1, a2 in zip(
                            typ1.argument_types, typ2.argument_types
                        )
                    )
                )
        elif isinstance(typ1, types.IndexableType):
            if isinstance(typ2, types.IndexableType) and type(typ1) is type(
                typ2
            ):
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
        elif isinstance(expr, expressions.UnaryOperator):
            return self.is_const_expr(expr.a)
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
            return self.is_const_expr(expr.variable.declaration)
        else:
            return False


class Scope:
    """ A variable scope """

    def __init__(self, parent=None):
        self.parent = parent

        # Different namespaces in this scope:
        self.var_map = OrderedDict()
        self._tags = OrderedDict()
        self.labels = OrderedDict()

    def get_defined_names(self):
        """ Get all defined symbols in this scope, and scopes above. """
        defined_names = []
        scope = self
        while scope is not None:
            for name in scope.var_map:
                defined_names.append(name)
            scope = scope.parent
        return defined_names

    def is_defined(self, name: str, all_scopes=True):
        """ Check if the name is defined """
        if name in self.var_map:
            return True
        elif self.parent and all_scopes:
            return self.parent.is_defined(name)
        else:
            return False

    def is_definition(self, name: str):
        """ Check if this name is a definition. """
        if self.is_defined(name, all_scopes=False):
            sym = self.get_identifier(name)
            return sym.declaration.is_definition()
        else:
            return False

    def insert(self, declaration: declarations.CDeclaration):
        """ Insert a variable into the current scope """
        assert isinstance(declaration, declarations.CDeclaration)
        assert declaration.name not in self.var_map
        symbol = Symbol(declaration.name)
        self.var_map[declaration.name] = symbol
        symbol.add_declaration(declaration)

    def update(self, declaration: declarations.CDeclaration):
        """ Update an existing name to a new declaration """
        assert isinstance(declaration, declarations.CDeclaration)
        assert declaration.name in self.var_map
        self.var_map[declaration.name].add_declaration(declaration)

    def get_declarations(self):
        r = []
        for s in self.var_map.values():
            d = s.declaration
            if isinstance(
                d, (declarations.EnumConstantDeclaration, declarations.Typedef)
            ):
                continue
            r.append(d)
        return r

    def has_tag(self, name: str, all_scopes=True):
        """ Check the tag namespace for the given name. """
        if name in self._tags:
            return True
        elif self.parent and all_scopes:
            return self.parent.has_tag(name)
        else:
            return False

    def get_tag(self, name: str, all_scopes=True):
        """ Get a struct by tag """
        if name in self._tags:
            return self._tags[name]
        elif self.parent and all_scopes:
            return self.parent.get_tag(name)
        else:
            raise KeyError(name)

    def add_tag(self, name: str, item):
        """ Add the given item to the tag namespace. """
        self._tags[name] = item

    def get_identifier(self, name: str):
        """ Get the symbol with the given name """
        if name in self.var_map:
            return self.var_map[name]
        elif self.parent:
            return self.parent.get_identifier(name)
        else:
            raise KeyError(name)


class Symbol:
    """ Intermediate layer inserted into the scope. """

    def __init__(self, name):
        self.name = name
        self.declarations = []

    @property
    def declaration(self):
        """ Return the best and most complete declaration for this symbol. """
        return self.declarations[-1]

    def is_definition(self):
        """ Test if this symbol is a definition. """
        return self.declaration.is_definition()

    @property
    def typ(self):
        return self.declaration.typ

    @property
    def location(self):
        return self.declaration.location

    def add_declaration(self, declaration):
        """ Append latest greatest declaration of this symbol. """
        self.declarations.append(declaration)

    def add_redeclaration(self, declaration):
        """ Append latest greatest declaration of this symbol. """
        if self.declaration.is_definition():
            assert not declaration.is_definition()
            self.declarations.insert(0, declaration)
        else:
            self.declarations.append(declaration)
