
import struct


class ElfHeader:
    pass


class ElfSection:
    pass


class ElfFile:
    """
        This class can load and save a elf file.
        https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
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
            = struct.unpack(self.E_FMT, f.read(48))
        return elf_file

    E_FMT = '<HHIQQQIHHHHHH'

    def save(self, f):
        e_ident = bytearray([0x7F, ord('E'), ord('L'), ord('F')] + [0]*12)
        # TODO: support 32 bit
        e_ident[4] = 2  # 1=32 bit, 2=64 bit
        e_ident[5] = 1  # 1=little endian, 2=big endian
        e_ident[6] = 1  # elf version = 1
        e_ident[7] = 3  # os abi (3 =linux)
        # rest is unused
        f.write(e_ident)

        # Write rest of header
        e_type = self.e_type
        e_machine = self.e_machine
        e_version = 1
        e_entry = 0x40000 + 64 + 56
        e_phoff = 64  # Follows this header
        e_shoff = 0  # section header offset
        e_flags = 0
        e_ehsize = 16 + struct.calcsize(self.E_FMT)  # size of this header
        e_phentsize = struct.calcsize(self.P_FMT)  # size of 1 program header
        e_phnum = 1  # number of program header entries
        e_shentsize = 0  # size of section header entries
        e_shnum = 0
        SHN_UNDEF = 0
        e_shstrndx = SHN_UNDEF  # Index into table with strings
        f.write(struct.pack(
            self.E_FMT, e_type, e_machine,
            e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize,
            e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx))

        for ph in range(1):
            self.write_program_header(f)
        for section in self.sections:
            f.write(section)
        for section in self.sections:
            # self.write_section_header(f)
            pass

    P_FMT = '<IIQQQQQQ'

    def write_program_header(self, f):
        p_type = 1  # 1=load
        p_flags = 5  # r,w,x
        p_offset = 0  # Load all file into memory!
        p_vaddr = 0x40000
        p_paddr = 0x40000
        p_filesz = 64 + 56 + len(self.sections[0])
        p_memsz = p_filesz
        p_align = 0x1000
        f.write(struct.pack(
            self.P_FMT, p_type, p_flags,
            p_offset, p_vaddr, p_paddr, p_filesz,
            p_memsz,
            p_align))

    SH_FMT = '<IIIQQIIIII'

    def write_section_header(self, f):
        sh_name = 0  # Index into string table
        sh_type = 0
        sh_flags = 0
        sh_addr = 0  # address in memory, else, 0
        sh_offset = 0  # Offset in file
        sh_size = 0  # Size of the section
        sh_link = 0
        sh_info = 0
        sh_addralign = 16
        sh_entsize = 0
        f.write(struct.pack(
            self.SH_FMT, sh_name, sh_type, sh_flags, sh_addr,
            sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize))
