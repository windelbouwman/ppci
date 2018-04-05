""" Clone of the famous `readelf` utility """


import argparse
from .base import base_parser, LogSetup
from ..formats.elf.file import read_elf, SectionHeaderType


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser])
parser.add_argument(
    'elf', help='ELF file', type=argparse.FileType('rb'))
parser.add_argument(
    '-a', '--all',
    help='Equivalent to: -h -l -S -s -r -d -V -A -I', action='store_true',
    default=False)
parser.add_argument(
    # '-h',  # TODO: conflicts with --help
    '--file-header',
    help='Display the ELF file header', action='store_true',
    default=False)
parser.add_argument(
    '-l', '--program-headers',
    help='Display the program headers', action='store_true',
    default=False)
parser.add_argument(
    '-S', '--section-headers',
    help='Display the section headers', action='store_true',
    default=False)
parser.add_argument(
    '-s', '--syms',
    help='Display the symbol table', action='store_true',
    default=False)
parser.add_argument(
    '-e', '--headers',
    help='Equivalent to: --file-header -l -S', action='store_true',
    default=False)


def readelf(args=None):
    """ Read ELF file and display contents """
    args = parser.parse_args(args)
    with LogSetup(args):
        elf = read_elf(args.elf)
        args.elf.close()
        print(elf)
        if args.file_header or args.all or args.headers:
            print_elf_header(elf.elf_header)

        if args.program_headers or args.all or args.headers:
            print_program_headers(elf.program_headers)

        if args.section_headers or args.all or args.headers:
            print_section_headers(elf.section_headers, elf)

        if args.syms or args.all:
            print_symbol_table(elf.symbol_table)


def print_elf_header(elf_header):
    elf_header.print()
    print()


def print_program_headers(program_headers):
    """ Print the program headers """
    print('Program headers:')
    print('  Type           Offset         VirtAddr         PhysAddr')
    print('              FileSiz           MemSiz  Flags  Align')
    for program_header in program_headers:
        print('  {}              0x{:016x} 0x{:016x} 0x{:016x}'.format(
            program_header['p_type'],
            program_header['p_offset'],
            program_header['p_vaddr'],
            program_header['p_paddr']
        ))
        print('                 0x{:016x} 0x{:016x}  {}  0x{:04x}'.format(
            program_header['p_filesz'],
            program_header['p_memsz'],
            program_header['p_flags'],
            program_header['p_align']
        ))
    print()


def print_section_headers(section_headers, elf_file):
    """ Print the section headers in a nice overview """
    print('Section headers:')
    print('  [Nr] Name   Type    Address   Offset')
    print('       Size   Entsize    Flags   Link Info Align')
    for index, section_header in enumerate(section_headers):
        print('  [{:2d}] {:16s}  {:16s} {:016x}  {:016x}'.format(
            index,
            elf_file.get_str(section_header['sh_name']),
            SectionHeaderType(section_header['sh_type']).name,
            section_header['sh_addr'],
            section_header['sh_offset']
        ))
        print('       {:016x}  {:016x} {} {} {} {}'.format(
            section_header['sh_size'],
            section_header['sh_entsize'],
            section_header['sh_flags'],
            section_header['sh_link'],
            section_header['sh_info'],
            section_header['sh_addralign']
        ))
    print()


def print_symbol_table(symbol_table):
    print('Symbol table:')
    print()


if __name__ == '__main__':
    readelf()
