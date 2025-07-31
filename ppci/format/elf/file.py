"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import io
import logging

from ...arch.arch_info import Endianness
from .headers import ElfMachine, HeaderTypes, SectionHeaderType


logger = logging.getLogger("elf")


class ElfRelocation:
    def __init__(self, header):
        self.header = header

    def __getitem__(self, key):
        if key == "type":
            #
        elif key == "symbol_id":
            #
        elif key == "section":
            #
        elif key == "offset":
            return header.r_offset
        elif key == "addend" and self.header.r_addend:
            return self.header.r_addend

    def parse_info(self):
        self.symbol_id = self.header.r_info >> 8

class ElfSection:
    def __init__(self, header):
        self.header = header

    def __getitem__(self, key):
        if key == "name" and self.name:
            return self.name
        elif key == "address":
            return self.header.sh_addr
        elif key == "data":
            return self.data
        elif key == "alignment":
            return self.header.addralign

    def read_data(self, f):
        """Read this elf section's data from file"""
        f.seek(self.header.sh_offset)
        self.data = f.read(self.header.sh_size)
        return self.data

    def get_str(self, offset):
        """Get a string indicated by numeric value"""
        end = self.data.find(0, offset)
        return self.data[offset:end].decode("utf8")


SHN_UNDEF = 0


class ElfFile:
    """This class can load and save a elf file."""

    e_version = 1

    def __init__(self, bits=64, endianness=Endianness.LITTLE):
        self.bits = bits
        self.e_machine = ElfMachine.X86_64  # x86-64 machine
        self.header_types = HeaderTypes(bits=bits, endianness=endianness)
        self.sections = []
        self.relocations = []

    def __getitem__(self, key):
        # enable conversion to ObjectFile
        if key == "arch":
            return self.e_machine.name.lower()
        elif key == "entry_symbol_id":
            return self.elf_header.e_entry # TODO: do not return when e_entry is 0
        elif key == "sections":
            return self.sections
        elif key == "relocations":
            return self.relocations

    @staticmethod
    def load(f):
        logger.debug("Loading ELF file")
        # Read header
        e_ident = f.read(16)
        if e_ident[0:4] != b"\x7fELF":
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
        elf_file.e_machine = ElfMachine(elf_file.elf_header.e_machine)

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
            typ = SectionHeaderType(section.header.sh_type)
            if typ == SectionHeaderType.REL:
                f.seek(section.header.sh_offset)
                rh = elf_file.header_types.RelocationTableEntry.read(f)
                elf_file.relocations.append(ElfRelocations(rh))
            elif typ == SectionHeaderType.RELA:
                f.seek(section.header.sh_offset)
                rh = elf_file.header_types.RelocationTableEntryWA.read(f)
                elf_file.relocations.append(ElfRelocations(rh))
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
        """Get a string indicated by numeric value"""
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
