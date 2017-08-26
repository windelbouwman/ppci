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
    LITTLE = 1
    BIG = 1000


class TypeInfo:
    """ Target specific type information """
    def __init__(self, size, alignment):
        self.size = size
        self.alignment = alignment


class ArchInfo:
    """ A collection of information for language frontends """
    def __init__(self, type_infos=None, endianness=Endianness.LITTLE):
        self.type_infos = type_infos
        self.endianness = endianness
        assert isinstance(endianness, Endianness)

    def get_type_info(self, typ):
        if isinstance(typ, str):
            typ = self.type_infos[typ]
        assert isinstance(typ, ir.Typ)
        return self.type_infos[typ]

    def get_size(self, typ):
        return self.get_type_info(typ).size
