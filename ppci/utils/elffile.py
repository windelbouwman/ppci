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


class ElfFile:
    """
        This class can load and save a elf file.
    """
    e_version = 1

    def __init__(self):
        self.e_type = 2  # Executable type
        self.e_machine = 0x3e  # x86-64 machine
        self.sections = []

    def add_section(self, data):
        self.sections.append(data)

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
        elf_file.e_type, elf_file.e_machine, _, _ \
            = struct.unpack(E_FMT, f.read(48))
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

        # Align to pages of 0x1000 (4096) bytes
        inter_spacing = 0x1000 - (tmp_offset % 0x1000)
        tmp_offset += inter_spacing

        offsets = {}
        for image in obj.images:
            offsets[image] = tmp_offset
            for section in image.sections:
                a = section.address - image.location
                offsets[section] = tmp_offset + a
            tmp_offset += image.size

        strtab = bytes([0])
        names = {}
        for section in obj.sections:
            if section.name not in names:
                names[section.name] = len(strtab)
                strtab += section.name.encode('ascii') + bytes([0])
        # TODO: insert extra sections here

        strtab_offset = tmp_offset
        tmp_offset += len(strtab)
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
        e_shnum = len(obj.sections) + 2
        e_shstrndx = len(obj.sections) + 1  # Index into table with strings
        f.write(struct.pack(
            E_FMT, e_type, e_machine,
            e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize,
            e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx))

        for image in obj.images:
            self.write_program_header(
                f, f_offset=offsets[image], vaddr=image.location,
                size=image.size)
        f.write(bytes(inter_spacing))
        for image in obj.images:
            f.write(image.data)
        f.write(strtab)   # symbols
        f.write(bytes(e_shentsize))  # Null section all zeros
        for section in obj.sections:
            self.write_section_header(
                f, offsets[section], vaddr=section.address,
                size=section.size, typ=SHT_PROGBITS, name=names[section.name],
                sh_flags=SHF_EXECINSTR | SHF_ALLOC)
        self.write_section_header(
            f, strtab_offset, size=len(strtab), typ=SHT_STRTAB)

    def write_program_header(self, f, f_offset=0, vaddr=0, size=0):
        p_type = 1  # 1=load
        p_flags = 5  # r,w,x
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
            self, f, offset, vaddr=0, size=0, typ=SHT_NULL,
            name=0, sh_flags=0):
        sh_name = name  # Index into string table
        sh_type = typ
        sh_addr = vaddr  # address in memory, else, 0
        sh_offset = offset  # Offset in file
        sh_size = size  # Size of the section
        sh_link = 0
        sh_info = 0
        sh_addralign = 4
        sh_entsize = 0
        f.write(struct.pack(
            SH_FMT, sh_name, sh_type, sh_flags, sh_addr,
            sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize))
