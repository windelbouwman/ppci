import logging
import struct
from ...common import CompilerError
from .symbol_table import Scope
from . import nodes


class Context:
    """ A global context for all pascal objects of a program.

    This is a replacement for the otherwise global variables during
    the processing of pascal code.
    """
    logger = logging.getLogger('pascal.context')

    def __init__(self, arch_info):
        self.root_scope = create_top_scope(arch_info)
        self.var_map = {}
        self.programs = []
        self.units = []

    def add_program(self, program):
        self.programs.append(program)

    def get_type(self, name, reveil_defined=True):
        if isinstance(name, nodes.Type):
            typ = name
        else:
            typ = self.root_scope.get_symbol(name)
            assert isinstance(typ, nodes.Type)

        if isinstance(typ, nodes.DefinedType) and reveil_defined:
            typ = self.get_type(typ.typ)

        return typ

    def equal_types(self, a, b, byname=False):
        """ Check if two types are equal """
        a = self.get_type(a)
        b = self.get_type(b)
        if type(a) is type(b):
            if isinstance(a, nodes.IntegerType):
                return a.bits == b.bits
            elif isinstance(a, nodes.PointerType):
                # If a pointed type is detected, stop structural
                # equivalence:
                return self.equal_types(a.ptype, b.ptype, byname=True)
            elif isinstance(a, nodes.DefinedType):
                # Try by name in case of defined types:
                return a.name == b.name
            elif isinstance(a, nodes.StructureType):
                if len(a.fields) != len(b.fields):
                    return False
                return all(self.equal_types(am.typ, bm.typ) for am, bm in
                           zip(a.fields, b.fields))
            elif isinstance(a, nodes.ArrayType):
                return self.equal_types(a.element_type, b.element_type)
            else:
                raise NotImplementedError(str(type(a)))

        return False

    def get_common_type(self, a, b, loc):
        """ Determine the greatest common type.

        This is used for coercing binary operators.
        For example
            int + float -> float
            byte + int -> int
            byte + byte -> byte
            pointer to x + int -> pointer to x
        """
        intType = self.get_type('integer')
        charType = self.get_type('char')
        table = {
            (intType, intType): intType,
            (intType, charType): intType,
            (charType, intType): intType,
            (charType, charType): charType,
            (intType, nodes.PointerType): intType,
        }
        typ_a = self.get_type(a.typ)
        typ_b = self.get_type(b.typ)

        if self.equal_types(typ_a, typ_b):
            return typ_a
        # Handle pointers:
        if isinstance(typ_a, nodes.PointerType) and \
                self.equal_types(typ_b, 'integer'):
            return typ_a

        # Handle non-pointers:
        key = (typ_a, typ_b)
        if key not in table:
            raise CompilerError(
                "Types {} and {} do not commute".format(typ_a, typ_b), loc)
        return table[(typ_a, typ_b)]

    def pack_string(self, txt):
        """ Pack a string an int as length followed by text data """
        length = self.pack_int(len(txt))
        data = txt.encode('ascii')
        return length + data

    def pack_int(self, v, bits=None, signed=True):
        if bits is None:
            bits = self.get_type('integer').byte_size * 8
        mapping = {
            (8, False): '<B', (8, True): '<b',
            (16, False): '<H', (16, True): '<h',
            (32, False): '<I', (32, True): '<i',
            (64, False): '<Q', (64, True): '<q'}
        fmt = mapping[(bits, signed)]
        return struct.pack(fmt, v)


def create_top_scope(arch_info):
    """ Create a scope that is the root of the scope tree.

    This includes the built-in types.
    """
    scope = Scope()

    # buildin types:
    int_type = nodes.SignedIntegerType('integer', arch_info.get_size('int'))
    scope.add_symbol(int_type)

    char_type = nodes.SignedIntegerType('char', 1)
    scope.add_symbol(char_type)

    bool_type = nodes.SignedIntegerType('bool', arch_info.get_size('int'))
    scope.add_symbol(bool_type)

    # Construct string type from others:
    len_field = nodes.StructField('len', int_type)
    txt = nodes.StructField('txt', nodes.ArrayType(char_type, 0))
    string_type = nodes.PointerType(nodes.StructureType([len_field, txt]))
    string_def_type = nodes.DefinedType('string', string_type, True, None)
    scope.add_symbol(string_def_type)

    return scope
