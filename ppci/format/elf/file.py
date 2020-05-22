"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import io
import logging

from ...arch.arch_info import Endianness
from ... import ir
from .headers import ElfMachine, HeaderTypes
from .headers import SectionHeaderType, SectionHeaderFlag
from .headers import SymbolTableBinding, SymbolTableType


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


def write_elf(obj, f, type="executable"):
    """ Save object as an ELF file.

    You can specify the type of ELF file with
    the type argument:
    - 'executable'
    - 'relocatable'
    """
    mapping = {
        "arm": (32, Endianness.LITTLE),
        "microblaze": (32, Endianness.BIG),
        "x86_64": (64, Endianness.LITTLE),
        "xtensa": (32, Endianness.LITTLE),
        "riscv": (32, Endianness.LITTLE),
    }
    bits, endianity = mapping[obj.arch.name]
    elf_file = ElfFile(bits=bits, endianness=endianity)
    etype_mapping = {
        "executable": ET_EXEC,
        "relocatable": ET_REL,
        # TODO: 'shared': ET_DYN,
    }
    e_type = etype_mapping[type]
    elf_file.save(f, obj, e_type)


# Elf types:
ET_NONE = 0
ET_REL = 1
ET_EXEC = 2
ET_DYN = 3
ET_CORE = 4
ET_NUM = 5
ET_LOOS = 0xFE00
ET_HIOS = 0xFEFF
ET_LOPROC = 0xFF00
ET_HIPROC = 0xFFFF


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
        bits = self.header_types.bits
        endianness = self.header_types.endianness
        bit_map = {32: 1, 64: 2}
        endianity_map = {Endianness.LITTLE: 1, Endianness.BIG: 2}
        machine_map = {
            "arm": ElfMachine.ARM,
            "microblaze": ElfMachine.MICROBLAZE,
            "x86_64": ElfMachine.X86_64,
            "xtensa": ElfMachine.XTENSA,
            "riscv": ElfMachine.RISCV,
        }
        self.e_machine = machine_map[obj.arch.name]
        self.e_type = e_type

        # Write identification:
        e_ident = bytearray([0x7F, ord("E"), ord("L"), ord("F")] + [0] * 12)
        e_ident[4] = bit_map[bits]  # 1=32 bit, 2=64 bit
        e_ident[5] = endianity_map[endianness]  # 1=little endian, 2=big endian
        e_ident[6] = 1  # elf version = 1
        e_ident[7] = 0  # os abi (3 =linux), 0=system V
        f.write(e_ident)

        logger.debug("Saving %s bits ELF file", bits)

        elf_header = self.header_types.ElfHeader()

        # Skip over elf header, will come back to this.
        f.seek(self.header_types.ElfHeader.size, io.SEEK_CUR)

        page_size = 0x1000
        file_offsets = {}

        if obj.images:
            # Skip over program headers, will come back to this.
            # size of 1 program header:
            elf_header.e_phoff = f.tell()
            elf_header.e_phentsize = self.header_types.ProgramHeader.size
            elf_header.e_phnum = len(obj.images)  # number of program headers
            f.seek(elf_header.e_phnum * elf_header.e_phentsize, io.SEEK_CUR)

            # Write sections contained in images:
            for image in obj.images:
                # Align to pages of 0x1000 (4096) bytes
                padding = page_size - (f.tell() % page_size)
                f.write(bytes(padding))
                file_offset = f.tell()
                assert file_offset % page_size == 0

                assert image not in file_offsets
                file_offsets[image] = file_offset
                for section in image.sections:
                    section_offset = section.address - image.address
                    assert section not in file_offsets
                    file_offsets[section] = file_offset + section_offset
                f.write(image.data)

        # Make the string table:
        string_table = StringTable()
        section_numbers = {}
        for i, section in enumerate(obj.sections, 1):
            string_table.get_name(section.name)
            section_numbers[section.name] = i

            # Write section which is not inside an image:
            if section not in file_offsets:
                # TODO: alignment of section??
                file_offset = f.tell()
                file_offsets[section] = file_offset
                f.write(section.data)

        # Create symbol table:
        # TODO: alignment?
        file_offsets[".symtab"] = f.tell()
        section_numbers[".symtab"] = len(obj.sections) + 1
        string_table.get_name(".symtab")
        symtab_entsize = self.header_types.SymbolTableEntry.size
        symtab_size = symtab_entsize * (len(obj.symbols) + 1)

        # Null symtab element (index 0):
        f.write(bytes(symtab_entsize))

        for symbol in obj.symbols:
            st_name = string_table.get_name(symbol.name)
            # TODO: sort by local / global (local first)
            if symbol.binding == ir.Binding.GLOBAL:
                st_bind = SymbolTableBinding.GLOBAL
            else:
                # TODO: change to LOCAL
                st_bind = SymbolTableBinding.GLOBAL
            st_type = SymbolTableType.NOTYPE
            st_info = (int(st_bind) << 4) | int(st_type)
            st_shndx = section_numbers[symbol.section]
            st_value = symbol.value + obj.get_section(symbol.section).address
            self.write_symbol_table_entry(
                f, st_name, st_info, 0, st_shndx, st_value
            )

        # Create relocation (rela) table:
        if self.e_type == ET_REL:
            elf_reloc_mapping = {
                "rel32": 2,  # guess: R_X86_64_PC32 ?
            }

            rela_entsize = self.header_types.RelocationTableEntry.size
            rela_size = rela_entsize * len(obj.relocations)

            # TODO: handle 32 bit r_info
            assert self.bits == 64

            # TODO: alignment?
            file_offsets[".relacode"] = f.tell()
            string_table.get_name(".relacode")

            for rel in obj.relocations:
                assert rel.section == "code"
                r_sym = rel.symbol_id + 1
                r_type = elf_reloc_mapping[rel.reloc_type]
                r_info = (r_sym << 32) + r_type
                rela_entry = self.header_types.RelocationTableEntry()
                rela_entry.r_offset = rel.offset
                rela_entry.r_info = r_info
                # TODO: Major hack to make rel32 work:
                rela_entry.r_addend = rel.addend - 4
                rela_entry.write(f)

        # Write string table (last section):
        # TODO: alignment?
        file_offsets[".strtab"] = f.tell()
        string_table.get_name(".strtab")
        strtab_size = len(string_table.strtab)
        f.write(string_table.strtab)

        # Section headers:

        # section header offset:
        elf_header.e_shoff = f.tell()

        # size of a single section header:
        elf_header.e_shentsize = self.header_types.SectionHeader.size

        # Number of section headers:
        if self.e_type == ET_REL:
            extra_sections = 4
        else:
            extra_sections = 3
        elf_header.e_shnum = len(obj.sections) + extra_sections

        # Index into table with strings:
        elf_header.e_shstrndx = len(obj.sections) + extra_sections - 1

        # Null section all zeros (index 0):
        f.write(bytes(elf_header.e_shentsize))
        for section in obj.sections:
            self.write_section_header(
                f,
                file_offsets[section],
                vaddr=section.address,
                sh_size=section.size,
                sh_type=SectionHeaderType.PROGBITS,
                name=string_table.get_name(section.name),
                sh_flags=SectionHeaderFlag.EXECINSTR | SectionHeaderFlag.ALLOC,
            )

        symbol_table_index_first_global = 1
        # symbol table (symtab):
        self.write_section_header(
            f,
            file_offsets[".symtab"],
            sh_size=symtab_size,
            sh_type=SectionHeaderType.SYMTAB,
            sh_entsize=symtab_entsize,
            sh_flags=SectionHeaderFlag.ALLOC,
            sh_link=elf_header.e_shstrndx,
            sh_info=symbol_table_index_first_global,
            name=string_table.get_name(".symtab"),
        )

        # Write rela section section header:
        if self.e_type == ET_REL:
            self.write_section_header(
                f,
                file_offsets[".relacode"],
                sh_size=rela_size,
                sh_type=SectionHeaderType.RELA,
                sh_entsize=rela_entsize,
                sh_flags=SectionHeaderFlag.INFO_LINK,
                sh_link=section_numbers[".symtab"],
                sh_info=section_numbers["code"],
                name=string_table.get_name(".relacode"),
            )

        # String table (strtab) = last section
        assert strtab_size == len(string_table.strtab)
        self.write_section_header(
            f,
            file_offsets[".strtab"],
            sh_size=strtab_size,
            sh_type=SectionHeaderType.STRTAB,
            sh_flags=SectionHeaderFlag.ALLOC,
            name=string_table.get_name(".strtab"),
        )

        # Write ELF header
        f.seek(16)
        elf_header.e_type = self.e_type
        elf_header.e_machine = self.e_machine
        elf_header.e_version = 1

        if obj.entry_symbol_id is None:
            if self.e_type == ET_EXEC:
                logger.warning(
                    "ELF file without an entry symbol specified. This file might crash."
                )
            elf_header.e_entry = 0
        else:
            elf_header.e_entry = obj.get_symbol_id_value(obj.entry_symbol_id)

        elf_header.e_flags = 0

        # Size of elf header + identification:
        elf_header.e_ehsize = 16 + self.header_types.ElfHeader.size

        # Write rest of header:
        elf_header.write(f)

        # Write program headers:
        for image in obj.images:
            if image.name == "code":
                p_flags = 5
            else:
                p_flags = 6
            self.write_program_header(
                f,
                f_offset=file_offsets[image],
                vaddr=image.address,
                size=image.size,
                p_flags=p_flags,
            )

    def write_symbol_table_entry(
        self, f, st_name, st_info, st_other, st_shndx, st_value, st_size=0
    ):
        symbol_table_entry = self.header_types.SymbolTableEntry()
        symbol_table_entry.st_name = st_name
        symbol_table_entry.st_info = st_info
        symbol_table_entry.st_other = st_other
        symbol_table_entry.st_shndx = st_shndx
        symbol_table_entry.st_value = st_value
        symbol_table_entry.st_size = st_size
        symbol_table_entry.write(f)

    def write_program_header(self, f, f_offset=0, vaddr=0, size=0, p_flags=4):
        program_header = self.header_types.ProgramHeader()
        program_header.p_type = 1  # 1=load
        program_header.p_flags = p_flags
        program_header.p_offset = f_offset  # Load all file into memory!
        program_header.p_vaddr = vaddr
        program_header.p_paddr = vaddr
        program_header.p_filesz = size
        program_header.p_memsz = size
        program_header.p_align = 0x1000
        program_header.write(f)

    def write_section_header(
        self,
        f,
        offset,
        vaddr=0,
        sh_size=0,
        sh_type=SectionHeaderType.NULL,
        name=0,
        sh_flags=0,
        sh_entsize=0,
        sh_link=0,
        sh_info=0,
    ):
        section_header = self.header_types.SectionHeader()
        section_header.sh_name = name  # Index into string table
        section_header.sh_type = sh_type.value
        section_header.sh_flags = sh_flags
        section_header.sh_addr = vaddr  # address in memory, else, 0
        section_header.sh_offset = offset  # Offset in file
        section_header.sh_size = sh_size
        section_header.sh_link = sh_link
        section_header.sh_info = sh_info
        section_header.sh_addralign = 4
        section_header.sh_entsize = sh_entsize
        section_header.write(f)
