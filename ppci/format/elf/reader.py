"""Support to process an ELF file."""

from .file import ElfFile
from .headers import SymbolTableBinding, SymbolTableType
from ...utils.binary_txt import asc2bin

# TODO: move some parts from ElfFile to this file.


def read_elf(f):
    """Read an ELF file"""
    return ElfFile.load(f)


def elf_to_object(f):
    from ppci.binutils.objectfile import ObjectFile, Section, RelocationEntry
    from ppci.arch import get_arch

    elf = read_elf(f)
    obj = ObjectFile(get_arch(elf.e_machine.name.lower()))

    if elf.elf_header.e_entry != 0:
        obj.entry_symbol_id = elf.elf_header.e_entry

    for s in elf.sections:
        so = Section(s.name)
        obj.add_section(so)
        so.address = s.header.sh_addr
        so.data = asc2bin(s.data)
        so.alignment = s.header.sh_addralign if s.header.sh_addralign else 1

    for r in elf.relocations:
        if r.header.r_addend:
            addend = r.header.r_addend
        else:
            addend = 0
        obj.add_relocation(
            RelocationEntry(
                r.type,
                r.symbol_id,
                r.section,
                r.header.r_offset,
                addend,
            )
        )

    if hasattr(elf, "symbole_table"):
        for sym in elf.symbole_table:
            obj.add_symbol(
                sym.i,
                sym.name,
                SymbolTableBinding(sym.binding).name.lower(),
                sym.header.st_value,
                sym.section.name,
                SymbolTableType(sym.type).name.lower(),
                sym.header.size,
            )
    return obj
