"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import io
import logging

from ...arch.arch_info import Endianness
from .headers import ElfMachine, HeaderTypes


logger = logging.getLogger("elf")


class ElfSection:
    def __init__(self, header):
        self.header = header

    def read_data(self, f):
        """ Read this elf section's data from file """
        f.seek(self.header.sh_offset)
        self.data = f.read(self.header.sh_size)
        return self.data

    def get_str(self, offset):
        """ Get a string indicated by numeric value """
        end = self.data.find(0, offset)
        return self.data[offset:end].decode("utf8")


SHN_UNDEF = 0


class StringTable:
    def __init__(self):
        self.strtab = bytes([0])
        self.names = {}

    def get_name(self, name):
        if name not in self.names:
            self.names[name] = len(self.strtab)
            self.strtab += name.encode("ascii") + bytes([0])
        return self.names[name]


class ElfFile:
    """ This class can load and save a elf file.
    """

    e_version = 1

    def __init__(self, bits=64, endianness=Endianness.LITTLE):
        self.bits = bits
        self.e_machine = ElfMachine.X86_64.value  # x86-64 machine
        self.header_types = HeaderTypes(bits=bits, endianness=endianness)
        self.sections = []

    @staticmethod
    def load(f):
        logger.debug("Loading ELF file")
        # Read header
        e_ident = f.read(16)
        if e_ident[0:4] != b"\x7FELF":
            raise ValueError("Not a valid ELF file")

        bits_map = {1: 32, 2: 64}
        bits = bits_map[e_ident[4]]
        endianity_map = {1: Endianness.LITTLE, 2: Endianness.BIG}
        endianity = endianity_map[e_ident[5]]

        elf_file = ElfFile(bits=bits, endianness=endianity)
        elf_file.e_ident = e_ident
        elf_file.ei_class = e_ident[4]

        # Read elf header:
        elf_file.elf_header = elf_file.header_types.ElfHeader.read(f)

        # Read program headers:
        elf_file.program_headers = []
        for _ in range(elf_file.elf_header.e_phnum):
            ph = elf_file.header_types.ProgramHeader.read(f)
            elf_file.program_headers.append(ph)

        # Read section headers:
        f.seek(elf_file.elf_header["e_shoff"])
        for _ in range(elf_file.elf_header["e_shnum"]):
            sh = elf_file.header_types.SectionHeader.read(f)
            elf_file.sections.append(ElfSection(sh))

        elf_file.read_strtab(f)
        for section in elf_file.sections:
            section.read_data(f)
            section.name = elf_file.get_str(section.header["sh_name"])
        return elf_file

    def read_strtab(self, f):
        self.strtab = self.sections[self.elf_header.e_shstrndx].read_data(f)

    def read_symbol_table(self, sym_section):
        f = io.BytesIO(sym_section.data)
        count = (
            len(sym_section.data) // self.header_types.SymbolTableEntry.size
        )
        table = [
            self.header_types.SymbolTableEntry.read(f) for _ in range(count)
        ]
        return table

    def get_str(self, offset):
        """ Get a string indicated by numeric value """
        end = self.strtab.find(0, offset)
        return self.strtab[offset:end].decode("utf8")

    def has_section(self, name):
        for section in self.sections:
            if section.name == name:
                return True
        return False

    def get_section(self, name):
        for section in self.sections:
            if section.name == name:
                return section
        raise KeyError(name)

    def save(self, f, obj, e_type):
        from .writer import ElfWriter

        writer = ElfWriter(f, self)
        writer.export_object(obj, e_type)
