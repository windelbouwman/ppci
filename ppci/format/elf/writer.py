"""Logic to write ELF files."""

import io
import logging
from collections import defaultdict
from ...arch.arch_info import Endianness
from ... import ir
from .headers import ElfMachine
from .headers import SectionHeaderType, SectionHeaderFlag
from .headers import SymbolTableBinding, SymbolTableType
from .headers import ProgramHeaderType
from .file import ElfFile
from .string import StringTable, elf_hash


logger = logging.getLogger("elf")


def write_elf(obj, f, type="executable"):
    """Save object as an ELF file.

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
        "shared": ET_DYN,
    }
    e_type = etype_mapping[type]
    writer = ElfWriter(f, elf_file)
    writer.export_object(obj, e_type)


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

# Dynamic tags:
DT_NULL = 0
DT_NEEDED = 1
DT_PLTRELSZ = 2
DT_PLTGOT = 3
DT_HASH = 4
DT_STRTAB = 5
DT_SYMTAB = 6
DT_RELA = 7
DT_RELASZ = 8
DT_RELAENT = 9
DT_STRSZ = 10
DT_SYMENT = 11
DT_INIT = 12
DT_FINI = 13
DT_SONAME = 14
DT_RPATH = 15
DT_SYMBOLIC = 16
DT_REL = 17
DT_RELSZ = 18
DT_RELENT = 19
DT_PLTREL = 20
DT_DEBUG = 21
DT_TEXTREL = 22
DT_JMPREL = 23
DT_LOPROC = 0x70000000
DT_HIPROC = 0x7FFFFFFF


machine_map = {
    "arm": ElfMachine.ARM,
    "microblaze": ElfMachine.MICROBLAZE,
    "x86_64": ElfMachine.X86_64,
    "xtensa": ElfMachine.XTENSA,
    "riscv": ElfMachine.RISCV,
}


class ElfWriter:
    """ELF file creator."""

    def __init__(self, f, elf_file):
        self.f = f
        self.elf_file = elf_file
        self.header_types = elf_file.header_types
        self.obj = None
        self.elf_header = None
        self.e_ident_size = 16

    def export_object(self, obj, e_type):
        """Main invocation point to generate an ELF file."""
        logger.debug("Saving %s bits ELF file", self.header_types.bits)
        self.obj = obj
        self.e_type = e_type

        self.write_identification()
        self.elf_header = self.elf_file.header_types.ElfHeader()
        self.program_headers = []
        self.section_headers = []
        self.string_table = StringTable()
        self.section_numbers = {}
        self.symbol_id_map = {}

        # Skip over elf header, will come back to this.
        self.f.seek(self.header_types.ElfHeader.size, io.SEEK_CUR)
        self.page_size = 0x1000

        if self.obj.images and self.e_type in [ET_EXEC, ET_DYN]:
            self.write_images()

        self.write_sections()
        self.write_symbol_table()

        if self.e_type == ET_REL:
            self.write_rela_table()
        elif self.e_type == ET_DYN:
            self.write_dynamic_section()

        self.write_string_table()
        self.write_section_headers()

        self.f.seek(self.e_ident_size)
        self.write_elf_header()
        self.write_program_headers()

    def write_identification(self):
        """Write ELF identification magic."""
        bits = self.header_types.bits
        endianness = self.header_types.endianness
        bit_map = {32: 1, 64: 2}
        endianity_map = {Endianness.LITTLE: 1, Endianness.BIG: 2}

        e_ident = bytearray([0x7F, ord("E"), ord("L"), ord("F")] + [0] * 12)
        e_ident[4] = bit_map[bits]  # 1=32 bit, 2=64 bit
        e_ident[5] = endianity_map[endianness]  # 1=little endian, 2=big endian
        e_ident[6] = 1  # elf version = 1
        e_ident[7] = 0  # os abi (3 =linux), 0=system V
        assert len(e_ident) == self.e_ident_size
        self.f.write(e_ident)

    def write_elf_header(self):
        """Write ELF header."""
        self.elf_header.e_type = self.e_type
        self.elf_header.e_machine = machine_map[self.obj.arch.name]
        self.elf_header.e_version = 1

        if self.e_type == ET_EXEC:
            if self.obj.entry_symbol_id is None:
                logger.warning(
                    "ELF file without an entry symbol specified."
                    "This file might crash."
                )
                self.elf_header.e_entry = 0
            else:
                self.elf_header.e_entry = self.obj.get_symbol_id_value(
                    self.obj.entry_symbol_id
                )

        self.elf_header.e_flags = 0

        # Size of elf header + identification:
        self.elf_header.e_ehsize = (
            self.e_ident_size + self.header_types.ElfHeader.size
        )

        # Index into table with strings:
        self.elf_header.e_shstrndx = self.section_numbers[".strtab"]

        # Write header:
        self.elf_header.write(self.f)

    def write_program_headers(self):
        """Write program headers"""
        assert self.elf_header.e_phnum == len(self.program_headers)
        for program_header in self.program_headers:
            program_header.write(self.f)

    def write_images(self):
        """Write images (segments in ELF speak) to file."""

        # Program header offset in file:
        self.elf_header.e_phoff = self.f.tell()

        # size of 1 program header:
        self.elf_header.e_phentsize = self.header_types.ProgramHeader.size

        # number of program headers:
        self.elf_header.e_phnum = len(self.obj.images)

        if self.e_type == ET_DYN:
            # Add dynamic section:
            self.elf_header.e_phnum += 1

        # Skip over program headers, will come back to this:
        self.f.seek(
            self.elf_header.e_phnum * self.elf_header.e_phentsize, io.SEEK_CUR
        )

        # Write sections contained in images:
        for image in self.obj.images:
            self.align_to(self.page_size)
            file_offset = self.f.tell()

            for section in image.sections:
                section_offset = section.address - image.address
                section_file_offset = file_offset + section_offset
                self.gen_section_header(section, section_file_offset)
            self.f.write(image.data)

            vaddr = image.address
            size = image.size
            if image.name == "code":
                p_flags = 5
            else:
                p_flags = 6

            # Create program header:
            program_header = self.header_types.ProgramHeader()
            program_header.p_type = ProgramHeaderType.LOAD
            program_header.p_flags = p_flags
            program_header.p_offset = file_offset
            program_header.p_vaddr = vaddr
            program_header.p_paddr = vaddr
            program_header.p_filesz = size
            program_header.p_memsz = size
            program_header.p_align = self.page_size
            self.program_headers.append(program_header)

    def write_sections(self):
        """Write section which is not inside an image."""
        for section in self.obj.sections:
            if section.name not in self.section_numbers:
                self.align_to(section.alignment)
                file_offset = self.f.tell()
                self.f.write(section.data)
                self.gen_section_header(section, file_offset)

    def gen_section_header(self, section, offset):
        """Create a section header for the given section.

        This header will be written to the section header table
        at the end of the file.
        """
        section_header = self.header_types.SectionHeader()
        section_header.sh_name = self.get_string(section.name)
        section_header.sh_type = SectionHeaderType.PROGBITS.value
        sh_flags = SectionHeaderFlag.ALLOC
        if section.name == "data":
            # Hmm, we should have an attribute on the section to
            # determine the type of section...
            sh_flags |= SectionHeaderFlag.WRITE
        else:
            sh_flags |= SectionHeaderFlag.EXECINSTR
        section_header.sh_flags = sh_flags
        section_header.sh_addr = section.address
        section_header.sh_offset = offset  # Offset in file
        section_header.sh_size = section.size
        section_header.sh_addralign = section.alignment
        self.section_headers.append(section_header)
        self.section_numbers[section.name] = len(self.section_headers)

    def write_symbol_table(self):
        """Create symbol table."""
        alignment = 8 if self.elf_file.bits == 64 else 4
        self.align_to(alignment)
        symtab_offset = self.f.tell()
        symtab_entsize = self.header_types.SymbolTableEntry.size
        symtab_size = symtab_entsize * (len(self.obj.symbols) + 1)

        # Split symbols in local and global symbols:
        local_symbols = []
        global_symbols = []
        for symbol in self.obj.symbols:
            if symbol.binding == ir.Binding.GLOBAL:
                global_symbols.append(symbol)
            else:
                local_symbols.append(symbol)

        # Null symtab element (index 0):
        self.f.write(bytes(symtab_entsize))

        symbol_table_types = {
            "func": SymbolTableType.FUNC,
            "object": SymbolTableType.OBJECT,
        }

        for nr, symbol in enumerate(local_symbols + global_symbols, 1):
            self.symbol_id_map[symbol.id] = nr

            if symbol.binding == ir.Binding.GLOBAL:
                st_bind = SymbolTableBinding.GLOBAL
            else:
                st_bind = SymbolTableBinding.LOCAL
            st_type = symbol_table_types.get(
                symbol.typ, SymbolTableType.NOTYPE
            )

            entry = self.header_types.SymbolTableEntry()
            entry.st_name = self.get_string(symbol.name)
            entry.st_info = (int(st_bind) << 4) | int(st_type)
            if symbol.defined:
                entry.st_shndx = self.section_numbers[symbol.section]
                entry.st_value = (
                    symbol.value + self.obj.get_section(symbol.section).address
                )
            else:
                entry.st_shndx = 0
                entry.st_value = 0
            entry.st_size = symbol.size
            entry.write(self.f)

        symbol_table_index_first_global = len(local_symbols) + 1

        section_header = self.header_types.SectionHeader()
        section_header.sh_name = self.get_string(".symtab")
        section_header.sh_type = SectionHeaderType.SYMTAB.value
        section_header.sh_flags = SectionHeaderFlag.ALLOC
        section_header.sh_offset = symtab_offset
        section_header.sh_size = symtab_size
        section_header.sh_link = 0  # filled later
        section_header.sh_info = symbol_table_index_first_global
        section_header.sh_addralign = alignment
        section_header.sh_entsize = symtab_entsize
        self.section_headers.append(section_header)
        self.section_numbers[".symtab"] = len(self.section_headers)

    def write_rela_table(self):
        """Create relocation (rela) table.

        Since a rela table is related to a single
        other section, we might require several rela
        tables, one per section.
        """
        alignment = 8 if self.elf_file.bits == 64 else 4
        sh_entsize = self.header_types.RelocationTableEntry.size

        # Create a table per section:
        reloc_groups = defaultdict(list)
        for rel in self.obj.relocations:
            reloc_groups[rel.section].append(rel)

        for section_name in sorted(reloc_groups):
            sh_size = sh_entsize * len(reloc_groups[section_name])

            self.align_to(alignment)
            rela_offset = self.f.tell()

            for rel in reloc_groups[section_name]:
                assert rel.section == section_name
                r_sym = self.symbol_id_map[rel.symbol_id]
                r_type = self.get_reloc_type(rel)

                if self.elf_file.bits == 64:
                    r_info = (r_sym << 32) + r_type
                else:
                    r_info = (r_sym << 8) + r_type

                rela_entry = self.header_types.RelocationTableEntry()
                rela_entry.r_offset = rel.offset
                rela_entry.r_info = r_info
                rela_entry.r_addend = rel.addend
                rela_entry.write(self.f)

            rela_name = ".rela" + section_name
            section_header = self.header_types.SectionHeader()
            section_header.sh_name = self.get_string(rela_name)
            section_header.sh_type = SectionHeaderType.RELA.value
            section_header.sh_flags = SectionHeaderFlag.INFO_LINK
            section_header.sh_offset = rela_offset
            section_header.sh_size = sh_size
            section_header.sh_link = 0  # symtab, to be filled later
            section_header.sh_info = self.section_numbers[section_name]
            section_header.sh_addralign = alignment
            section_header.sh_entsize = sh_entsize
            self.section_headers.append(section_header)

    def get_reloc_type(self, rel):
        symbol = self.obj.symbols_by_id[rel.symbol_id]
        r_type = self.obj.arch.get_reloc_type(rel.reloc_type, symbol)
        return r_type

    def write_string_table(self):
        """Write string table (last section)"""
        alignment = 1
        self.align_to(alignment)

        strtab_offset = self.f.tell()
        sh_name = self.get_string(".strtab")
        strtab_size = len(self.string_table.strtab)
        self.f.write(self.string_table.strtab)

        assert strtab_size == len(self.string_table.strtab)
        section_header = self.header_types.SectionHeader()
        section_header.sh_name = sh_name
        section_header.sh_type = SectionHeaderType.STRTAB.value
        section_header.sh_flags = SectionHeaderFlag.ALLOC
        section_header.sh_offset = strtab_offset
        section_header.sh_size = strtab_size
        section_header.sh_addralign = alignment
        self.section_headers.append(section_header)
        self.section_numbers[".strtab"] = len(self.section_headers)

    def write_section_headers(self):
        """Write section header table into file."""
        self.align_to(8)

        # section header offset:
        self.elf_header.e_shoff = self.f.tell()

        # size of a single section header:
        self.elf_header.e_shentsize = self.header_types.SectionHeader.size

        # Number of section headers:
        self.elf_header.e_shnum = len(self.section_headers) + 1

        # Null section all zeros (index 0):
        self.f.write(bytes(self.elf_header.e_shentsize))

        for section_header in self.section_headers:
            # Patch in some forward links:
            if section_header.sh_type == SectionHeaderType.SYMTAB.value:
                section_header.sh_link = self.section_numbers[".strtab"]
            elif section_header.sh_type == SectionHeaderType.DYNAMIC.value:
                section_header.sh_link = self.section_numbers[".strtab"]
            elif section_header.sh_type == SectionHeaderType.RELA.value:
                section_header.sh_link = self.section_numbers[".symtab"]
            section_header.write(self.f)

    def write_dynamic_section(self):
        """Create dynamic instruction table.

        The dynamic table includes instruction for
        the runtime to execute.

        """

        # Create dynamic contraption:
        Entry = self.header_types.DynamicEntry
        instructions = []

        def emit(tag, val):
            entry = Entry()
            entry.d_tag = tag
            entry.d_val = val
            instructions.append(entry)

        # DT_NEEDED libc.so.6
        emit(DT_NEEDED, self.get_string("libc.so.6"))
        emit(DT_NULL, 0)

        # TODO: figure out how to generate this info properly

        # DT_HASH
        # DT_STRTAB
        # DT_SYMTAB
        # DT_STRSZ
        # DT_SYMENT

        # Write dynamic table to file:
        alignment = 8 if self.elf_file.bits == 64 else 4
        self.align_to(alignment)
        dynamic_file_offset = self.f.tell()
        for ins in instructions:
            ins.write(self.f)
        dynamic_size = len(instructions) * Entry.size

        # Create program header:
        p_flags = 6
        # TODO: where to place the dynamic section in memory?
        vaddr = 0x60000000
        program_header = self.header_types.ProgramHeader()
        program_header.p_type = ProgramHeaderType.DYNAMIC
        program_header.p_flags = p_flags
        program_header.p_offset = dynamic_file_offset
        program_header.p_vaddr = vaddr
        program_header.p_paddr = vaddr
        program_header.p_filesz = dynamic_size
        program_header.p_memsz = dynamic_size
        program_header.p_align = alignment
        self.program_headers.append(program_header)

        # Create section header:
        section_header = self.header_types.SectionHeader()
        section_header.sh_name = self.get_string(".dynamic")
        section_header.sh_type = SectionHeaderType.DYNAMIC
        section_header.sh_addr = vaddr
        section_header.sh_flags = SectionHeaderFlag.ALLOC
        section_header.sh_offset = dynamic_file_offset
        section_header.sh_size = dynamic_size
        section_header.sh_link = 0  # filled later
        section_header.sh_info = 0
        section_header.sh_addralign = alignment
        section_header.sh_entsize = Entry.size
        self.section_headers.append(section_header)
        self.section_numbers[".dynamic"] = len(self.section_headers)

    def create_hash_table(self):
        """Create hash table for fast symbol lookup.

        This is used by the dynamic loader when looking
        up many symbols.
        """
        # Same amount as symbol table
        nchains = len(self.obj.symbols) + 1
        nbuckets = 8
        buckets = [0] * nbuckets
        chain = [0] * nchains
        for symbol in self.obj.symbols:
            symbol_index = self.symbol_id_map[symbol.id]
            hash_value = elf_hash(symbol.name)
            bucket_index = hash_value % nbuckets
            if buckets[bucket_index] == 0:
                # empty bucket
                buckets[bucket_index] = symbol_index
            else:
                # follow chain until empty slot.
                chain_index = buckets[bucket_index]
                while chain[chain_index] != 0:
                    chain_index = chain[chain_index]
                chain[chain_index] = symbol_index

    def align_to(self, alignment):
        padding = (alignment - (self.f.tell() % alignment)) % alignment
        self.f.write(bytes(padding))
        assert self.f.tell() % alignment == 0

    def get_string(self, txt: str) -> int:
        """Enter text in the string table and return the offset."""
        return self.string_table.get_name(txt)
