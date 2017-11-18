""" Architecture information carriers.

This module contains classes with information about a specific target.

The information present:
- endianness
- type sizes and alignment
- int size for the machine

"""
import enum
from .. import ir


class Endianness(enum.Enum):
    """ Define endianness as little or big """
    LITTLE = 1
    BIG = 1000


class TypeInfo:
    """ Target specific type information """
    def __init__(self, size, alignment):
        self.size = size
        self.alignment = alignment


class ArchInfo:
    """ A collection of information for language frontends """
    def __init__(
            self, type_infos=None, endianness=Endianness.LITTLE,
            register_classes=()):
        self.type_infos = type_infos
        assert isinstance(endianness, Endianness)
        self.endianness = endianness
        self.register_classes = register_classes

        mapping = {}
        for register_class in self.register_classes:
            for ty in register_class.ir_types:
                if ty in mapping:
                    raise ValueError('Duplicate type assignment {}'.format(ty))
                mapping[ty] = register_class.typ
        self.value_classes = mapping

    def get_type_info(self, typ):
        """ Retrieve type information for the given type """
        if isinstance(typ, str):
            typ = self.type_infos[typ]
        assert isinstance(typ, ir.Typ)
        return self.type_infos[typ]

    def get_size(self, typ):
        """ Get the size (in bytes) of the given type """
        return self.get_type_info(typ).size

    def get_alignment(self, typ):
        """ Get the alignment for the given type """
        return self.get_type_info(typ).alignment
