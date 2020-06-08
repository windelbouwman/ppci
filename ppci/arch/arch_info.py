""" Architecture information carriers.

This module contains classes with information about a specific target.

The information present:
- endianness
- type sizes and alignment
- int size for the machine

"""
import enum
from .. import ir
from collections import defaultdict
from ..utils.collections import OrderedSet


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
        self,
        type_infos=None,
        endianness=Endianness.LITTLE,
        register_classes=(),
    ):
        self.type_infos = type_infos
        assert isinstance(endianness, Endianness)
        self.endianness = endianness
        self.register_classes = register_classes
        self._registers_by_name = {}

        mapping = {}
        for register_class in self.register_classes:
            for ty in register_class.ir_types:
                if ty in mapping:
                    raise ValueError("Duplicate type assignment {}".format(ty))
                mapping[ty] = register_class.typ
            if register_class.registers:
                for register in register_class.registers:
                    self._registers_by_name[register.name] = register
        self.value_classes = mapping

        self.calc_alias()

    def get_register(self, name):
        """ Retrieve the machine register by name. """
        return self._registers_by_name[name]

    def has_register(self, name):
        """ Test if this architecture has a register with the given name. """
        return name in self._registers_by_name

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

    def calc_alias(self):
        """ Calculate a complete overview of register aliasing.

        This uses the alias attribute when a register is
        defined.

        For example on x86_64, `rax` aliases with `eax`, `eax` aliases `ax`,
        and `ax` aliases `al`.

        This function creates a map from `al` to `rax` and vice versa.
        """
        alias = defaultdict(OrderedSet)

        for reg_class in self.register_classes:
            if reg_class.registers:
                for register in reg_class.registers:
                    # The trivial alias: itself!
                    alias[register].add(register)
                    for r2 in dfs_alias(register):
                        alias[register].add(r2)
                        alias[r2].add(register)

        self.alias = dict(alias)


def dfs_alias(register):
    """ Do a depth first search on the aliases member.

    This can be used to find aliases of aliases.
    """
    for r2 in register.aliases:
        for r3 in dfs_alias(r2):
            yield r3
        yield r2
