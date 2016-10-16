import logging
import operator
import struct
from .scope import create_top_scope, Scope, SemanticError
from . import astnodes as ast


class Context:
    """ A context is the space where all modules live in.

    It is actually the container of modules and the top
    level scope.
    """
    logger = logging.getLogger('c3ctx')

    def __init__(self, arch):
        self.scope = create_top_scope(arch)
        self.module_map = {}
        self.const_map = {}
        self.var_map = {}    # Maps variables to storage locations.
        self.const_workset = set()
        self.pointerSize = arch.byte_sizes['ptr']

    def has_module(self, name):
        """ Check if a module with the given name exists """
        return name in self.module_map

    def get_module(self, name, create=True):
        """ Gets or creates the module with the given name """
        if name not in self.module_map and create:
            module = ast.Module(name, Scope(self.scope), None)
            self.module_map[name] = module
        return self.module_map[name]

    @property
    def modules(self):
        """ Get all the modules in this context """
        return self.module_map.values()

    def link_imports(self):
        """ Resolve all modules referenced by other modules """
        self.logger.debug('Resolving imports')
        for mod in self.modules:
            for imp in mod.imports:
                if self.has_module(imp):
                    if mod.inner_scope.has_symbol(imp):
                        raise SemanticError("Redefine of {}".format(imp))
                    mod.inner_scope.add_symbol(self.get_module(imp))
                else:
                    raise SemanticError('Cannot import {}'.format(imp))

    def resolve_symbol(self, ref):
        """ Find out what is designated with x """
        if isinstance(ref, ast.Member):
            base = self.resolve_symbol(ref.base)
            if not isinstance(base, ast.Module):
                raise SemanticError('Base is not a module', ref.loc)
            scope = base.inner_scope
            name = ref.field

            # Take into account access attribute!
            if scope.has_symbol(name):
                sym = scope.get_symbol(name)
                if not sym.public:
                    raise SemanticError(
                        'Cannot access private {}'.format(name), ref.loc)
            else:
                raise SemanticError('{} undefined'.format(name), ref.loc)
        elif isinstance(ref, ast.Identifier):
            # Simple identifier, try to lookup!
            scope = ref.scope
            name = ref.target
            if scope.has_symbol(name):
                sym = scope[name]
            else:
                raise SemanticError('{} undefined'.format(name), ref.loc)
        else:  # pragma: no cover
            raise NotImplementedError(str(ref))

        assert isinstance(sym, ast.Symbol)
        return sym

    def get_constant_value(self, const):
        """ Get the constant value, calculate if required """
        assert isinstance(const, ast.Constant)
        if const not in self.const_map:
            if const in self.const_workset:
                varnames = ', '.join(wc.name for wc in self.const_workset)
                msg = 'Constant loop detected involving: {}'.format(varnames)
                raise SemanticError(msg, const.loc)
            self.const_workset.add(const)
            self.const_map[const] = self.eval_const(const.value)
            self.const_workset.remove(const)
        return self.const_map[const]

    def eval_const(self, expr):
        """ Evaluates a constant expression. """

        # TODO: check types!!
        assert isinstance(expr, ast.Expression), str(expr) + str(type(expr))
        if isinstance(expr, ast.Literal):
            return expr.val
        elif isinstance(expr, ast.Binop):
            a = self.eval_const(expr.a)
            b = self.eval_const(expr.b)
            ops = {
                '+': operator.add,
                '-': operator.sub,
                '/': operator.truediv,
                '*': operator.mul,
                '%': operator.mod,
                }
            return ops[expr.op](a, b)
        elif isinstance(expr, ast.TypeCast):
            a = self.eval_const(expr.a)
            if self.equal_types('int', expr.to_type):
                return int(a)
            elif self.equal_types('byte', expr.to_type):
                return int(a) & 0xFF
            else:  # pragma: no cover
                raise NotImplementedError(
                    'Casting to {} not implemented'.format(expr.to_type))
        elif isinstance(expr, ast.Identifier):
            target = self.resolve_symbol(expr)
            if isinstance(target, ast.Constant):
                return self.get_constant_value(target)
            else:
                raise SemanticError('Cannot evaluate {}'.format(expr), None)
        else:
            raise SemanticError('Cannot evaluate constant {}'
                                .format(expr), None)

    def pack_string(self, txt):
        """ Pack a string an int as length followed by text data """
        length = self.pack_int(len(txt))
        data = txt.encode('ascii')
        return length + data

    def pack_int(self, v):
        mapping = {1: '<B', 2: '<H', 4: '<I', 8: '<Q'}
        fmt = mapping[self.get_type('int').byte_size]
        return struct.pack(fmt, v)

    def get_common_type(self, a, b, loc):
        """ Determine the greatest common type.

        This is used for coercing binary operators.
        For example
            int + float -> float
            byte + int -> int
            byte + byte -> byte
            pointer to x + int -> pointer to x
        """
        intType = self.get_type('int')
        byteType = self.get_type('byte')
        floatType = self.get_type('float')
        doubleType = self.get_type('double')
        table = {
            (intType, intType): intType,
            (intType, byteType): intType,
            (intType, doubleType): doubleType,
            (intType, floatType): floatType,
            (floatType, intType): floatType,
            (floatType, doubleType): doubleType,
            (doubleType, floatType): doubleType,
            (byteType, intType): intType,
            (byteType, byteType): byteType,
            (byteType, byteType): byteType,
            (intType, ast.PointerType): intType,
            }
        typ_a = self.get_type(a.typ)
        typ_b = self.get_type(b.typ)

        if self.equal_types(typ_a, typ_b):
            return typ_a
        # Handle pointers:
        if isinstance(typ_a, ast.PointerType) and \
                self.equal_types(typ_b, 'int'):
            return typ_a

        # Handle non-pointers:
        key = (typ_a, typ_b)
        if key not in table:
            raise SemanticError(
                "Types {} and {} do not commute".format(typ_a, typ_b), loc)
        return table[(typ_a, typ_b)]

    def get_type(self, typ, reveil_defined=True):
        """ Get type given by str, identifier or type.

        When reveil_defined is True, defined types are resolved to
        their backing types.
        """
        # Convenience:
        if isinstance(typ, str):
            typ = self.scope[typ]

        # Find the type:
        if isinstance(typ, ast.DefinedType):
            if reveil_defined:
                typ = self.get_type(typ.typ)
        elif isinstance(typ, (ast.Identifier, ast.Member)):
            typ = self.get_type(self.resolve_symbol(typ), reveil_defined)

        assert isinstance(typ, ast.Type)
        return typ

    def is_simple_type(self, typ):
        """ Determines if the given type is a simple type """
        typ = self.get_type(typ)
        return isinstance(typ, (ast.PointerType, ast.BaseType))

    def size_of(self, typ):
        """ Determine the byte size of a type """
        typ = self.get_type(typ)

        if isinstance(typ, ast.BaseType):
            return typ.byte_size
        elif isinstance(typ, ast.StructureType):
            return sum(self.size_of(mem.typ) for mem in typ.fields)
        elif isinstance(typ, ast.ArrayType):
            if isinstance(typ.size, ast.Expression):
                num = self.eval_const(typ.size)
            else:
                num = int(typ.size)
            assert isinstance(num, int)
            return num * self.size_of(typ.element_type)
        elif isinstance(typ, ast.PointerType):
            return self.pointerSize
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def equal_types(self, a, b, byname=False):
        """ Compare types a and b for structural equavalence.
            if byname is True stop on defined types.
        """
        # Recurse into named types:
        a = self.get_type(a, not byname)
        b = self.get_type(b, not byname)

        # Do structural equivalence check:
        if type(a) is type(b):
            if isinstance(a, ast.BaseType):
                return a.name == b.name
            elif isinstance(a, ast.PointerType):
                # If a pointed type is detected, stop structural
                # equivalence:
                return self.equal_types(a.ptype, b.ptype, byname=True)
            elif isinstance(a, ast.StructureType):
                if len(a.fields) != len(b.fields):
                    return False
                return all(self.equal_types(am.typ, bm.typ) for am, bm in
                           zip(a.fields, b.fields))
            elif isinstance(a, ast.ArrayType):
                return self.equal_types(a.element_type, b.element_type)
            elif isinstance(a, ast.DefinedType):
                # Try by name in case of defined types:
                return a.name == b.name
            else:  # pragma: no cover
                raise NotImplementedError('{} not implemented'.format(type(a)))
        return False
