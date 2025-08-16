"""Collection of data structures to handle elf files"""

import enum

from .. import header
from ...arch.arch_info import Endianness


class OsAbi(enum.IntEnum):
    SYSTEMV = 0
    HPUX = 1
    NETBSD = 2
    LINUX = 3
    GNUHURD = 4
    SOLARIS = 6
    AIX = 7
    IRIX = 8
    FREEBSD = 0x9
    TRU64 = 0xA
    NOVELL_MODESTO = 0xB
    OPENBSD = 0xC
    OPENVMS = 0xD
    NONSTOP_KERNEL = 0xE
    AROS = 0xF
    FENIX_OS = 0x10
    CLOUDABI = 0x11

    @classmethod
    def has_value(cls, value):
        return any(value == i.value for i in cls)


def get_os_name(value):
    """Given an integer value, try to get some name for an OS."""
    if OsAbi.has_value(value):
        name = OsAbi(value).name
    else:
        name = f"Unknown: {value}"
    return name


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
    SHLIB = 0xA
    DYNSYM = 0xB
    INIT_ARRAY = 0xE
    FINI_ARRAY = 0xF
    PREINIT_ARRAY = 0x10
    GROUP = 0x11
    SYMTAB_SHNDX = 0x12
    NUM = 0x13
    LOOS = 0x60000000

    @classmethod
    def _missing_(cls, value):
        return cls.NULL


class SectionHeaderFlag(enum.IntEnum):
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
    NONE = 0
    M32 = 1
    SPARC = 0x2
    X86 = 0x3
    _68K = 4
    _88K = 5
    IAMCU = 6
    _860 = 7
    MIPS = 0x8
    S370 = 0x9
    MIPS_RS3_LE = 10
    POWERPC = 0x14  # 20
    PPC64 = 21
    S390 = 0x16  # 22
    SPU = 23
    ARM = 0x28
    SUPERH = 0x2A
    H8S = 48
    X86_64 = 0x3E  # 62
    AVR = 83
    FR30 = 84
    D10V = 85
    D30V = 86
    V850 = 87
    M32R = 88
    MN10300 = 89
    MN10200 = 90
    PJ = 91
    OPENRISC = 92
    ARC_COMPACT = 93
    XTENSA = 0x5E  # 94
    VIDEOCORE = 0x5F  # 95
    TMM_GPP = 96
    AARCH64 = 0xB7  # 183
    STM8 = 186
    TILE64 = 187
    TILEPRO = 188
    MICROBLAZE = 189
    CUDA = 190
    TILEGX = 191
    CLOUDSHIELD = 192
    RISCV = 0xF3  # 243

    @classmethod
    def has_value(cls, value):
        return any(value == i.value for i in cls)


def get_machine_name(value):
    """Given an integer value, try to get some name for a machine."""
    if ElfMachine.has_value(value):
        name = ElfMachine(value).name
    else:
        name = f"Unknown: {value}"
    return name


class ProgramHeaderType(enum.IntEnum):
    NULL = 0
    LOAD = 1
    DYNAMIC = 2
    INTERP = 3
    NOTE = 4
    SHLIB = 5
    PHDR = 6
    TLS = 7
    LOOS = 0x60000000
    LOPROC = 0x70000000
    HIPROC = 0x7FFFFFFF


class SymbolTableBinding(enum.IntEnum):
    LOCAL = 0
    GLOBAL = 1
    WEAK = 2
    LOOS = 10
    HIOS = 12
    LOPROC = 13
    HIPROC = 15


def get_symbol_table_binding_name(value):
    if value in range(SymbolTableBinding.LOOS, SymbolTableBinding.HIOS + 1):
        name = f"OS: {value}"
    elif value in range(
        SymbolTableBinding.LOPROC, SymbolTableBinding.HIPROC + 1
    ):
        name = f"PROC: {value}"
    else:
        name = SymbolTableBinding(value).name
    return name


class SymbolTableType(enum.IntEnum):
    NOTYPE = 0
    OBJECT = 1
    FUNC = 2
    SECTION = 3
    FILE = 4
    COMMON = 5
    TLS = 6
    LOOS = 10
    HIOS = 12
    LOPROC = 13
    HIPROC = 15


def get_symbol_table_type_name(value):
    if value in range(SymbolTableType.LOOS, SymbolTableType.HIOS + 1):
        name = f"OS: {value}"
    elif value in range(SymbolTableType.LOPROC, SymbolTableType.HIPROC + 1):
        name = f"PROC: {value}"
    else:
        name = SymbolTableType(value).name
    return name


class HeaderTypes:
    """ELF header types for a given bitsize and endianity"""

    def __init__(self, bits=64, endianness=Endianness.LITTLE):
        self.bits = bits
        self.endianness = endianness

        if bits == 64:
            self.ElfHeader = header.mk_header(
                "ElfHeader",
                [
                    header.Uint16("e_type"),
                    header.Uint16("e_machine"),
                    header.Uint32("e_version"),
                    header.Uint64("e_entry"),
                    header.Uint64("e_phoff"),
                    header.Uint64("e_shoff"),
                    header.Uint32("e_flags"),
                    header.Uint16("e_ehsize"),
                    header.Uint16("e_phentsize"),
                    header.Uint16("e_phnum"),
                    header.Uint16("e_shentsize"),
                    header.Uint16("e_shnum"),
                    header.Uint16("e_shstrndx"),
                ],
            )
            assert self.ElfHeader.size + 16 == 64
        else:
            self.ElfHeader = header.mk_header(
                "ElfHeader",
                [
                    header.Uint16("e_type"),
                    header.Uint16("e_machine"),
                    header.Uint32("e_version"),
                    header.Uint32("e_entry"),
                    header.Uint32("e_phoff"),
                    header.Uint32("e_shoff"),
                    header.Uint32("e_flags"),
                    header.Uint16("e_ehsize"),
                    header.Uint16("e_phentsize"),
                    header.Uint16("e_phnum"),
                    header.Uint16("e_shentsize"),
                    header.Uint16("e_shnum"),
                    header.Uint16("e_shstrndx"),
                ],
            )
            assert self.ElfHeader.size + 16 == 0x34

        if bits == 32:
            self.SectionHeader = header.mk_header(
                "SectionHeader",
                [
                    header.Uint32("sh_name"),
                    header.Uint32("sh_type"),
                    header.Uint32("sh_flags"),
                    header.Uint32("sh_addr"),
                    header.Uint32("sh_offset"),
                    header.Uint32("sh_size"),
                    header.Uint32("sh_link"),
                    header.Uint32("sh_info"),
                    header.Uint32("sh_addralign"),
                    header.Uint32("sh_entsize"),
                ],
            )
            assert self.SectionHeader.size == 0x28
        else:
            self.SectionHeader = header.mk_header(
                "SectionHeader",
                [
                    header.Uint32("sh_name"),
                    header.Uint32("sh_type"),
                    header.Uint64("sh_flags"),
                    header.Uint64("sh_addr"),
                    header.Uint64("sh_offset"),
                    header.Uint64("sh_size"),
                    header.Uint32("sh_link"),
                    header.Uint32("sh_info"),
                    header.Uint64("sh_addralign"),
                    header.Uint64("sh_entsize"),
                ],
            )
            assert self.SectionHeader.size == 0x40

        if bits == 64:
            self.ProgramHeader = header.mk_header(
                "ProgramHeader",
                [
                    header.Uint32("p_type"),
                    header.Uint32("p_flags"),
                    header.Uint64("p_offset"),
                    header.Uint64("p_vaddr"),
                    header.Uint64("p_paddr"),
                    header.Uint64("p_filesz"),
                    header.Uint64("p_memsz"),
                    header.Uint64("p_align"),
                ],
            )
            assert self.ProgramHeader.size == 0x38
        else:
            self.ProgramHeader = header.mk_header(
                "ProgramHeader",
                [
                    header.Uint32("p_type"),
                    header.Uint32("p_offset"),
                    header.Uint32("p_vaddr"),
                    header.Uint32("p_paddr"),
                    header.Uint32("p_filesz"),
                    header.Uint32("p_memsz"),
                    header.Uint32("p_flags"),
                    header.Uint32("p_align"),
                ],
            )
            assert self.ProgramHeader.size == 0x20

        if bits == 64:
            self.SymbolTableEntry = header.mk_header(
                "SymbolTableEntry",
                [
                    header.Uint32("st_name"),
                    header.Uint8("st_info"),
                    header.Uint8("st_other"),
                    header.Uint16("st_shndx"),
                    header.Uint64("st_value"),
                    header.Uint64("st_size"),
                ],
            )
            assert self.SymbolTableEntry.size == 24
        else:
            self.SymbolTableEntry = header.mk_header(
                "SymbolTableEntry",
                [
                    header.Uint32("st_name"),
                    header.Uint32("st_value"),
                    header.Uint32("st_size"),
                    header.Uint8("st_info"),
                    header.Uint8("st_other"),
                    header.Uint16("st_shndx"),
                ],
            )
            assert self.SymbolTableEntry.size == 16

        if bits == 64:
            self.RelocationTableEntryWA = header.mk_header(
                "RelocationTableEntryWA",
                [
                    header.Uint64("r_offset"),
                    header.Uint64("r_info"),
                    header.Int64("r_addend"),
                ],
            )
            assert self.RelocationTableEntryWA.size == 24
        else:
            self.RelocationTableEntryWA = header.mk_header(
                "RelocationTableEntryWA",
                [
                    header.Uint32("r_offset"),
                    header.Uint32("r_info"),
                    header.Int32("r_addend"),
                ],
            )
            assert self.RelocationTableEntryWA.size == 12

        if bits == 64:
            self.RelocationTableEntry = header.mk_header(
                "RelocationTableEntry",
                [
                    header.Uint64("r_offset"),
                    header.Uint64("r_info"),
                ],
            )
            assert self.RelocationTableEntry.size == 16
        else:
            self.RelocationTableEntry = header.mk_header(
                "RelocationTableEntry",
                [
                    header.Uint32("r_offset"),
                    header.Uint32("r_info"),
                ],
            )
            assert self.RelocationTableEntry.size == 8

        if bits == 64:
            self.DynamicEntry = header.mk_header(
                "DynamicEntry",
                [
                    header.Int64("d_tag"),
                    header.Uint64("d_val"),
                ],
            )
            assert self.DynamicEntry.size == 16
        else:
            self.DynamicEntry = header.mk_header(
                "DynamicEntry",
                [
                    header.Int32("d_tag"),
                    header.Uint32("d_val"),
                ],
            )
            assert self.DynamicEntry.size == 8
