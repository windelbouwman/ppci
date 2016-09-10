"""
Implementation for the ELF file format.

https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
"""

import struct


class ElfHeader:
    pass


class ElfSection:
    pass


SH_FMT = '<IIQQQQIIQQ'
E_FMT = '<HHIQQQIHHHHHH'
P_FMT = '<IIQQQQQQ'
SYM_FMT = '<IBBHQQ'

SHN_UNDEF = 0

SHT_NULL = 0x0
SHT_PROGBITS = 0x1
SHT_SYMTAB = 0x2
SHT_STRTAB = 0x3
SHT_HASH = 0x5
SHT_NOTE = 0x7

SHF_WRITE = 0x1
SHF_ALLOC = 0x2
SHF_EXECINSTR = 0x4


class StringTable:
    def __init__(self):
        self.strtab = bytes([0])
        self.names = {}

    def get_name(self, name):
        if name not in self.names:
            self.names[name] = len(self.strtab)
            self.strtab += name.encode('ascii') + bytes([0])
        return self.names[name]


class ElfFile:
    """
        This class can load and save a elf file.
    """
    e_version = 1

    def __init__(self):
        self.e_type = 2  # Executable type
        self.e_machine = 0x3e  # x86-64 machine

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
        # elf_file.e_type, elf_file.e_machine, _, _ \
        #    = struct.unpack(E_FMT, f.read(48))
        return elf_file

    def save(self, f, obj):
        # TODO: support 32 bit

        # Write identification:
        e_ident = bytearray([0x7F, ord('E'), ord('L'), ord('F')] + [0]*12)
        e_ident[4] = 2  # 1=32 bit, 2=64 bit
        e_ident[5] = 1  # 1=little endian, 2=big endian
        e_ident[6] = 1  # elf version = 1
        e_ident[7] = 0  # os abi (3 =linux), 0=system V
        f.write(e_ident)

        e_phentsize = struct.calcsize(P_FMT)  # size of 1 program header
        assert e_phentsize == 56
        e_phnum = len(obj.images)  # number of program header entries

        # Determine offsets into file:
        tmp_offset = 64 + e_phnum * e_phentsize

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
                a = section.address - image.location
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
        e_shoff = tmp_offset  # section header offset

        # Write rest of header
        e_type = self.e_type
        e_machine = self.e_machine
        e_version = 1
        e_entry = 0x40000
        e_phoff = 64  # Follows this header
        e_flags = 0
        e_ehsize = 16 + struct.calcsize(E_FMT)
        assert 64 == e_ehsize  # size of this header
        e_shentsize = struct.calcsize(SH_FMT)  # size of section header
        assert 64 == e_shentsize
        e_shnum = len(obj.sections) + 3
        e_shstrndx = len(obj.sections) + 1  # Index into table with strings
        # symtab is at +2

        # Write rest of header:
        f.write(struct.pack(
            E_FMT, e_type, e_machine,
            e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize,
            e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx))

        # Program headers:
        for image in obj.images:
            if image.name == 'code':
                p_flags = 5
            else:
                p_flags = 6
            self.write_program_header(
                f, f_offset=offsets[image], vaddr=image.location,
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
        f.write(bytes(e_shentsize))  # Null section all zeros
        for section in obj.sections:
            self.write_section_header(
                f, offsets[section], vaddr=section.address,
                sh_size=section.size, sh_type=SHT_PROGBITS,
                name=string_table.get_name(section.name),
                sh_flags=SHF_EXECINSTR | SHF_ALLOC)
        assert strtab_size == len(string_table.strtab)
        self.write_section_header(
            f, strtab_offset, sh_size=strtab_size, sh_type=SHT_STRTAB,
            sh_flags=SHF_ALLOC, name=string_table.get_name('.strtab'))
        self.write_section_header(
            f, symtab_offset, sh_size=symtab_size, sh_type=SHT_SYMTAB,
            sh_entsize=symtab_entsize, sh_flags=SHF_ALLOC, sh_link=e_shstrndx,
            name=string_table.get_name('.symtab'))

    def write_symbol_table_entry(
            self, f, st_name, st_info, st_other,
            st_shndx, st_value, st_size=0):
        f.write(
            struct.pack(
                SYM_FMT, st_name, st_info, st_other, st_shndx,
                st_value, st_size))

    def write_program_header(self, f, f_offset=0, vaddr=0, size=0, p_flags=4):
        p_type = 1  # 1=load
        p_offset = f_offset  # Load all file into memory!
        p_vaddr = vaddr
        p_paddr = vaddr
        p_filesz = size
        p_memsz = size
        p_align = 0x1000
        f.write(struct.pack(
            P_FMT, p_type, p_flags,
            p_offset, p_vaddr, p_paddr, p_filesz,
            p_memsz,
            p_align))

    def write_section_header(
            self, f, offset, vaddr=0, sh_size=0, sh_type=SHT_NULL,
            name=0, sh_flags=0, sh_entsize=0, sh_link=0):
        sh_name = name  # Index into string table
        sh_addr = vaddr  # address in memory, else, 0
        sh_offset = offset  # Offset in file
        sh_info = 0
        sh_addralign = 4
        f.write(struct.pack(
            SH_FMT, sh_name, sh_type, sh_flags, sh_addr,
            sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize))
