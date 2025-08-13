"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import io
import logging

from ...arch.arch_info import Endianness
from .headers import (
    ElfMachine,
    HeaderTypes,
    SectionHeaderType,
    SymbolTableBinding,
    SymbolTableType,
)


logger = logging.getLogger("elf")


class ElfRelocation:
    def __init__(self, header, bits=64):
        self.header = header
        self.bits = bits
        self.parse_info()

    def __getitem__(self, key):
        if key == "type":
            return self.type
        elif key == "symbol_id":
            return self.symbol_id
        elif key == "section":
            return self.section
        elif key == "offset":
            return hex(self.header.r_offset)
        elif key == "addend":
            if self.header.r_addend:
                return hex(self.header.r_addend)
            else:
                return hex(0)
        else:
            raise IndexError

    def parse_info(self):
        if self.bits == 64:
            self.symbol_id = self.header.r_info >> 32
            self.type = self.header.r_info & 0xFFFFFFFF
        else:
            self.symbol_id = self.header.r_info >> 8
            self.type = self.header.r_info & 0xFF

    def connect_section(self, symbole_table, sections):
        symbole = symbole_table[self.symbol_id].header
        self.section = sections[symbole.st_shndx].name


class ElfSymbol:
    def __init__(self, header, i):
        self.header = header
        self.i = i
        self.parse_info()

    def __getitem__(self, key):
        if key == "binding":
            return SymbolTableBinding(self.binding).name.lower()
        elif key == "id":
            return self.i
        elif key == "name":
            return self.name
        elif key == "section":
            return self.section.name
        elif key == "size":
            return self.header.st_size
        elif key == "typ":
            return SymbolTableType(self.type).name.lower()
        elif key == "value":
            return str(hex(self.header.st_value))
        else:
            raise IndexError

    def parse_info(self):
        self.binding = self.header.st_info >> 4
        self.type = self.header.st_info & 0xF


class ElfSection:
    def __init__(self, header):
        self.header = header

    def __getitem__(self, key):
        if key == "name":
            return self.name
        elif key == "address":
            return hex(self.header.sh_addr)
        elif key == "data":
            return self.data
        elif key == "alignment":
            if self.header.sh_addralign == 0:
                return (
                    "0x1"  # set the alignment to 1 if there is none specified
                )
            else:
                return hex(self.header.sh_addralign)
        else:
            raise IndexError

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
            return (
                self.elf_header.e_entry
            )  # TODO: do not return when e_entry is 0
        elif key == "sections":
            return self.sections
        elif key == "relocations":
            return self.relocations
        elif key == "symbols":
            if hasattr(self, "symbole_table"):
                return self.symbole_table
            else:
                return []
        elif key == "images":
            return []
        else:
            raise IndexError

    def __contains__(self, key):
        if key == "entry_symbol_id" and self.elf_header.e_entry == 0:
            return False
        return key in [
            "arch",
            "entry_symbol_id",
            "sections",
            "relocations",
            "symbols",
        ]

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
            section.name = elf_file.get_str(
                section.header["sh_name"], elf_file.strtab
            )
            typ = SectionHeaderType(section.header["sh_type"])
            if typ == SectionHeaderType.REL:
                f.seek(section.header["sh_offset"])
                rh = elf_file.header_types.RelocationTableEntry.read(f)
                elf_file.relocations.append(ElfRelocation(rh, bits=bits))
            elif typ == SectionHeaderType.RELA:
                f.seek(section.header.sh_offset)
                rh = elf_file.header_types.RelocationTableEntryWA.read(f)
                elf_file.relocations.append(ElfRelocation(rh, bits=bits))
            elif typ in [SectionHeaderType.SYMTAB, SectionHeaderType.DYNSYM]:
                elf_file.symbole_table = elf_file.read_symtab(section)
            elif typ == SectionHeaderType.STRTAB and section.name in [
                ".strtab",
                ".dynstr",
            ]:
                elf_file.symstrtab = section.read_data(f)

        if "symbole_table" in vars(elf_file):
            for relocation in elf_file.relocations:
                relocation.connect_section(
                    elf_file.symbole_table, elf_file.sections
                )
            for symbol in elf_file.symbole_table:
                symbol.name = elf_file.get_str(
                    symbol.header["st_name"], elf_file.symstrtab
                )
                if symbol.header.st_shndx < len(elf_file.sections):
                    symbol.section = elf_file.sections[symbol.header.st_shndx]
        return elf_file

    def read_strtab(self, f):
        self.strtab = self.sections[self.elf_header.e_shstrndx].read_data(f)

    def read_symtab(self, sym_section):
        f = io.BytesIO(sym_section.data)
        count = (
            len(sym_section.data) // self.header_types.SymbolTableEntry.size
        )
        table = [
            ElfSymbol(self.header_types.SymbolTableEntry.read(f), i)
            for i in range(count)
        ]
        return table

    def read_symbol_table(self, f):
        return [s.header for s in self.symbole_table]

    def get_str(self, offset, *strtab):
        """Get a string indicated by numeric value"""
        if len(strtab) == 0:
            strtab = self.strtab
        else:
            strtab = strtab[0]
        end = strtab.find(0, offset)
        return strtab[offset:end].decode("utf8")

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
