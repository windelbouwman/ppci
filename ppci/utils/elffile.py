"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import struct
import enum
from .elf.headers import ElfHeader, SectionHeader, ProgramHeader


# ElfIdent = mk_header([
#    UByte('ei_ident') * 12,
#    Padding(7)
# ])


# Elf64Header = mk_header([
#    Half('e_type'),
#    Padding(7)
# ])


class ElfSection:
    pass



SYM_FMT = '<IBBHQQ'

SHN_UNDEF = 0


class SectionHeaderType(enum.IntEnum):
    NULL = 0x0
    PROGBITS = 0x1
    SYMTAB = 0x2
    STRTAB = 0x3
    RELA = 0x4
    HASH = 0x5
    DYNAMIC = 0x6
    NOTE = 0x7
    NOBITS = 0x8
    REL = 0x9
    SHLIB = 0xa
    DYNSYM = 0xb
    INIT_ARRAY = 0xe
    FINI_ARRAY = 0xf
    PREINIT_ARRAY = 0x10
    GROUP = 0x11
    SYMTAB_SHNDX = 0x12
    NUM = 0x13


class SectionHeaderFlag(enum.IntFlag):
    WRITE = 0x1
    ALLOC = 0x2
    EXECINSTR = 0x4
    MERGE = 0x10
    STRINGS = 0x20
    INFO_LINK = 0x40
    LINK_ORDER = 0x80
    OS_NONCONFORMING = 0x100
    GROUP = 0x200
    TLS = 0x400


class ElfMachine(enum.IntEnum):
    SPARC = 0x2
    X86 = 0x3
    MIPS = 0x8
    POWERPC = 0x14
    S390 = 0x16
    ARM = 0x28
    SUPERH = 0x2A
    X86_64 = 0x3e
    AARCH64 = 0xb7
    RISCV = 0xF3


class StringTable:
    def __init__(self):
        self.strtab = bytes([0])
        self.names = {}

    def get_name(self, name):
        if name not in self.names:
            self.names[name] = len(self.strtab)
            self.strtab += name.encode('ascii') + bytes([0])
        return self.names[name]


def read_elf(f):
    """ Read an ELF file """
    return ElfFile.load(f)


class ElfFile:
    """
        This class can load and save a elf file.
    """
    e_version = 1

    def __init__(self):
        self.e_type = 2  # Executable type
        self.e_machine = ElfMachine.X86_64.value  # x86-64 machine

    @staticmethod
    def load(f):
        elf_file = ElfFile()
        # Read header
        e_ident = f.read(16)
        assert e_ident[0] == 0x7F
        assert e_ident[1] == ord('E')
        assert e_ident[2] == ord('L')
        assert e_ident[3] == ord('F')
        elf_file.ei_class = e_ident[4]

        # Read elf header:
        elf_file.elf_header = ElfHeader.read(f)
        elf_file.program_headers = []
        for _ in range(elf_file.elf_header.e_phnum):
            ph = ProgramHeader.read(f)
            elf_file.program_headers.append(ph)

        f.seek(elf_file.elf_header['e_shoff'])
        elf_file.section_headers = []
        for _ in range(elf_file.elf_header['e_shnum']):
            sh = SectionHeader.read(f)
            elf_file.section_headers.append(sh)

        elf_file.read_strtab(f)
        return elf_file

    def read_strtab(self, f):
        section_header = self.section_headers[self.elf_header.e_shstrndx]
        f.seek(section_header.sh_offset)
        self.strtab = f.read(section_header.sh_size)

    def get_str(self, offset):
        """ Get a string indicated by numeric value """
        end = self.strtab.find(0, offset)
        return self.strtab[offset:end].decode('utf8')

    def save(self, f, obj):
        # TODO: support 32 bit

        # Write identification:
        e_ident = bytearray([0x7F, ord('E'), ord('L'), ord('F')] + [0]*12)
        e_ident[4] = 2  # 1=32 bit, 2=64 bit
        e_ident[5] = 1  # 1=little endian, 2=big endian
        e_ident[6] = 1  # elf version = 1
        e_ident[7] = 0  # os abi (3 =linux), 0=system V
        f.write(e_ident)

        elf_header = ElfHeader()
        elf_header.e_phentsize = ProgramHeader.size  # size of 1 program header
        assert elf_header.e_phentsize == 56
        elf_header.e_phnum = len(obj.images)  # number of program headers

        # Determine offsets into file:
        tmp_offset = 64 + elf_header.e_phnum * elf_header.e_phentsize

        # Determine offsets into the file of sections and images:
        offsets = {}
        pre_padding = {}
        for image in obj.images:
            # Align to pages of 0x1000 (4096) bytes
            inter_spacing = 0x1000 - (tmp_offset % 0x1000)
            tmp_offset += inter_spacing
            pre_padding[image] = inter_spacing

            offsets[image] = tmp_offset
            for section in image.sections:
                a = section.address - image.address
                offsets[section] = tmp_offset + a
            tmp_offset += image.size

        # Make the string table:
        string_table = StringTable()
        section_numbers = {}
        for i, section in enumerate(obj.sections):
            string_table.get_name(section.name)
            section_numbers[section.name] = i + 1
        string_table.get_name('.symtab')
        string_table.get_name('.strtab')

        # Create symbol table:
        symtab_offset = tmp_offset
        symtab_entsize = struct.calcsize(SYM_FMT)
        symtab_size = (len(obj.symbols) + 1) * symtab_entsize
        for symbol in obj.symbols:
            string_table.get_name(symbol.name)
        tmp_offset += symtab_size

        # Reserve space for string table:
        strtab_offset = tmp_offset
        strtab_size = len(string_table.strtab)
        tmp_offset += strtab_size

        # Write rest of header
        elf_header.e_type = self.e_type
        elf_header.e_machine = self.e_machine
        elf_header.e_version = 1
        elf_header.e_entry = 0x40000
        elf_header.e_phoff = 64  # Follows this header
        elf_header.e_shoff = tmp_offset  # section header offset
        elf_header.e_flags = 0
        elf_header.e_ehsize = 16 + ElfHeader.size
        assert 64 == elf_header.e_ehsize  # size of this header
        elf_header.e_shentsize = SectionHeader.size  # size of section header
        assert 64 == elf_header.e_shentsize
        elf_header.e_shnum = len(obj.sections) + 3

        # Index into table with strings:
        elf_header.e_shstrndx = len(obj.sections) + 1
        # symtab is at +2

        # Write rest of header:
        elf_header.write(f)

        # Program headers:
        for image in obj.images:
            if image.name == 'code':
                p_flags = 5
            else:
                p_flags = 6
            self.write_program_header(
                f, f_offset=offsets[image], vaddr=image.address,
                size=image.size, p_flags=p_flags)

        # Write actually program data:
        for image in obj.images:
            f.write(bytes(pre_padding[image]))
            f.write(image.data)

        # Symbol table:
        f.write(bytes(symtab_entsize))  # Null symtab element
        for symbol in obj.symbols:
            st_name = string_table.get_name(symbol.name)
            st_info = 0
            st_shndx = section_numbers[symbol.section]
            st_value = symbol.value + obj.get_section(symbol.section).address
            self.write_symbol_table_entry(
                f, st_name, st_info, 0, st_shndx, st_value)

        # String table:
        f.write(string_table.strtab)

        # Sections:
        f.write(bytes(elf_header.e_shentsize))  # Null section all zeros
        for section in obj.sections:
            self.write_section_header(
                f, offsets[section], vaddr=section.address,
                sh_size=section.size, sh_type=SectionHeaderType.PROGBITS,
                name=string_table.get_name(section.name),
                sh_flags=SectionHeaderFlag.EXECINSTR | SectionHeaderFlag.ALLOC)
        assert strtab_size == len(string_table.strtab)
        self.write_section_header(
            f, strtab_offset, sh_size=strtab_size,
            sh_type=SectionHeaderType.STRTAB,
            sh_flags=SectionHeaderFlag.ALLOC,
            name=string_table.get_name('.strtab'))
        self.write_section_header(
            f, symtab_offset, sh_size=symtab_size,
            sh_type=SectionHeaderType.SYMTAB,
            sh_entsize=symtab_entsize, sh_flags=SectionHeaderFlag.ALLOC,
            sh_link=elf_header.e_shstrndx,
            name=string_table.get_name('.symtab'))

    def write_symbol_table_entry(
            self, f, st_name, st_info, st_other,
            st_shndx, st_value, st_size=0):
        f.write(
            struct.pack(
                SYM_FMT, st_name, st_info, st_other, st_shndx,
                st_value, st_size))

    def write_program_header(self, f, f_offset=0, vaddr=0, size=0, p_flags=4):
        program_header = ProgramHeader()
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
            self, f, offset, vaddr=0, sh_size=0,
            sh_type=SectionHeaderType.NULL,
            name=0, sh_flags=0, sh_entsize=0, sh_link=0):
        section_header = SectionHeader()
        section_header.sh_name = name  # Index into string table
        section_header.sh_type = sh_type.value
        section_header.sh_flags = sh_flags
        section_header.sh_addr = vaddr  # address in memory, else, 0
        section_header.sh_offset = offset  # Offset in file
        section_header.sh_size = sh_size
        section_header.sh_link = sh_link
        section_header.sh_info = 0
        section_header.sh_addralign = 4
        section_header.sh_entsize = sh_entsize
        section_header.write(f)
