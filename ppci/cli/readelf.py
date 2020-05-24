""" Clone of the famous `readelf` utility """


import argparse
from .base import base_parser, LogSetup
from ..utils.hexdump import hexdump
from ..format.elf import read_elf
from ..format.elf.headers import SectionHeaderType
from ..format.elf.headers import get_symbol_table_type_name
from ..format.elf.headers import get_symbol_table_binding_name
from ..format.elf.headers import ProgramHeaderType, get_machine_name
from ..format.elf.headers import get_os_name


parser = argparse.ArgumentParser(description=__doc__, parents=[base_parser])
parser.add_argument("elf", help="ELF file", type=argparse.FileType("rb"))
parser.add_argument(
    "-a",
    "--all",
    help="Equivalent to: -h -l -S -s -r -d -V -A -I",
    action="store_true",
    default=False,
)
parser.add_argument(
    # '-h',  # TODO: conflicts with --help
    "--file-header",
    help="Display the ELF file header",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-l",
    "--program-headers",
    help="Display the program headers",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-S",
    "--section-headers",
    help="Display the section headers",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-s",
    "--syms",
    help="Display the symbol table",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-e",
    "--headers",
    help="Equivalent to: --file-header -l -S",
    action="store_true",
    default=False,
)
parser.add_argument(
    "-x", "--hex-dump", help="Dump contents of section as bytes", default=None
)
parser.add_argument(
    "--debug-dump",
    choices=("rawline", ""),
    help="Display contents of dwarf sections",
    default=None,
)


def readelf(args=None):
    """ Read ELF file and display contents """
    args = parser.parse_args(args)
    with LogSetup(args):
        # Read in elf file:
        elf = read_elf(args.elf)
        args.elf.close()

        # Dump information:
        if args.file_header or args.all or args.headers:
            print_elf_header(elf)

        if args.program_headers or args.all or args.headers:
            print_program_headers(elf.program_headers)

        if args.section_headers or args.all or args.headers:
            print_section_headers(elf)

        if args.syms or args.all:
            print_symbol_table(elf)

        if args.hex_dump:
            section_number = int(args.hex_dump)
            print_hex_dump(elf, section_number)

        if args.debug_dump:
            print_debug_info(elf, args.debug_dump)


def print_elf_header(elf):
    """ Print the ELF header fields """
    print("ELF Header:")
    magic = " ".join("{:02x}".format(v) for v in elf.e_ident)
    print("  Magic:", magic)
    print("  Class:", elf.ei_class)
    print("  Data:", elf.e_ident[5])  # EI_DATA = 5
    print("  Version:", elf.e_ident[6])  # EI_VERSION = 6
    os_abi = get_os_name(elf.e_ident[7])  # EI_OSABI = 7
    print("  OS/ABI:", os_abi)
    print("  ABI Version:", elf.e_ident[8])  # EI_ABIVERSION = 8
    print("  Type:", elf.elf_header["e_type"])
    machine = get_machine_name(elf.elf_header["e_machine"])
    print("  Machine:", machine)
    print("  Version:", elf.elf_header["e_version"])
    print("  Entry point address:", hex(elf.elf_header["e_entry"]))
    print(
        "  Start of program headers:",
        elf.elf_header["e_phoff"],
        "(bytes into file)",
    )
    print(
        "  Start of section headers:",
        elf.elf_header["e_shoff"],
        "(bytes into file)",
    )
    print("  Flags:", elf.elf_header["e_flags"])
    print("  Size of this header:", elf.elf_header["e_ehsize"], "(bytes)")
    print(
        "  Size of program headers:", elf.elf_header["e_phentsize"], "(bytes)"
    )
    print("  Number of program headers:", elf.elf_header["e_phnum"])
    print(
        "  Size of section headers:", elf.elf_header["e_shentsize"], "(bytes)"
    )
    print("  Number of section headers:", elf.elf_header["e_shnum"])
    print("  Section header string table index:", elf.elf_header["e_shstrndx"])
    print()


def print_program_headers(program_headers):
    """ Print the program headers """
    print("Program headers:")
    print("  Type             Offset         VirtAddr         PhysAddr")
    print("              FileSiz           MemSiz  Flags  Align")
    for program_header in program_headers:
        p_type = program_header["p_type"]
        if p_type < ProgramHeaderType.LOOS:
            p_type = ProgramHeaderType(p_type).name

        print(
            "  {:16} 0x{:016x} 0x{:016x} 0x{:016x}".format(
                p_type,
                program_header["p_offset"],
                program_header["p_vaddr"],
                program_header["p_paddr"],
            )
        )
        print(
            "                 0x{:016x} 0x{:016x}  {}  0x{:04x}".format(
                program_header["p_filesz"],
                program_header["p_memsz"],
                program_header["p_flags"],
                program_header["p_align"],
            )
        )
    print()


def print_section_headers(elf_file):
    """ Print the section headers in a nice overview """
    print("Section headers:")
    print("  [Nr] Name              Type             Address           Offset")
    print("       Size              Entsize          Flags   Link Info  Align")
    for index, section in enumerate(elf_file.sections):
        sh_type = section.header["sh_type"]
        if sh_type < SectionHeaderType.LOOS:
            sh_type = SectionHeaderType(sh_type).name
        print(
            "  [{:2d}] {:16s}  {:16} {:016x}  {:016x}".format(
                index,
                elf_file.get_str(section.header["sh_name"]),
                sh_type,
                section.header["sh_addr"],
                section.header["sh_offset"],
            )
        )
        print(
            "       {:016x}  {:016x} {} {} {} {}".format(
                section.header["sh_size"],
                section.header["sh_entsize"],
                section.header["sh_flags"],
                section.header["sh_link"],
                section.header["sh_info"],
                section.header["sh_addralign"],
            )
        )
    print()


def print_symbol_table(elf_file):
    """ Print the symbol table out """
    sym_types = [SectionHeaderType.DYNSYM, SectionHeaderType.SYMTAB]
    for sym_section in elf_file.sections:
        if sym_section.header.sh_type in sym_types:
            name_section = elf_file.sections[sym_section.header.sh_link]
            print_symbols(elf_file, sym_section, name_section)


def print_symbols(elf_file, sym_section, name_section):
    print("Symbol table {}:".format(sym_section.name))
    print("  Num: Value             Size Type    Bind     Vis   Ndx Name")
    table = elf_file.read_symbol_table(sym_section)
    for idx, row in enumerate(table):
        name = name_section.get_str(row["st_name"])
        bind = get_symbol_table_binding_name(row["st_info"] >> 4)
        typ = get_symbol_table_type_name(row["st_info"] & 0xF)
        vis = 0  # TODO: what is this?
        print(
            "  {:3d}: {:016x}  {:4} {:7} {:7} {:4d} {:5d} {}".format(
                idx,
                row["st_value"],
                row["st_size"],
                typ,
                bind,
                vis,
                row["st_shndx"],
                name,
            )
        )
    print()


def print_hex_dump(elf, section_number):
    print("Hex dump of section {}:".format(section_number))
    data = elf.sections[section_number].data
    hexdump(data)
    print()


def print_debug_info(elf, what):
    """ Print out debug information in the ELF file """
    if what == "rawline":
        print("Raw dump of section .debug_line:")
        section = elf.get_section(".debug_line")
        # program = dwarf.read_line_program(section.data)
        hexdump(section.data)
        print()
    else:
        raise NotImplementedError(what)


if __name__ == "__main__":
    readelf()
