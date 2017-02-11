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

    def __init__(self, arch):
        self.arch = arch
        self.root_scope = create_top_scope(arch)
        self.var_map = {}
        self.programs = []
        self.units = []

    def add_program(self, program):
        self.programs.append(program)

    def get_type(self, name):
        if isinstance(name, nodes.Type):
            return name
        else:
            symbol = self.root_scope.get_symbol(name)
            assert isinstance(symbol, nodes.Type)
            return symbol

    def equal_types(self, a, b):
        """ Check if two types are equal """
        a = self.get_type(a)
        b = self.get_type(b)
        if type(a) is type(b):
            if isinstance(a, nodes.IntegerType):
                return a.bits == b.bits
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


def create_top_scope(arch):
    """ Create a scope that is the root of the scope tree.

    This includes the built-in types.
    """
    scope = Scope()

    # buildin types:
    int_type = nodes.SignedIntegerType('integer', arch.byte_sizes['int'])
    scope.add_symbol(int_type)

    char_type = nodes.SignedIntegerType('char', 1)
    scope.add_symbol(char_type)

    bool_type = nodes.SignedIntegerType('bool', arch.byte_sizes['int'])
    scope.add_symbol(bool_type)

    # Construct string type from others:
    len_field = nodes.StructField('len', int_type)
    txt = nodes.StructField('txt', nodes.ArrayType(char_type, 0))
    string_type = nodes.PointerType(nodes.StructureType([len_field, txt]))
    string_def_type = nodes.DefinedType('string', string_type, True, None)
    scope.add_symbol(string_def_type)

    return scope
