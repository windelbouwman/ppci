"""Support to process an ELF file."""

from .file import ElfFile
from .../binutils/objectfile.py import ObjectFile, Section

# TODO: move some parts from ElfFile to this file.


def read_elf(f):
    """Read an ELF file"""
    return ElfFile.load(f)

def elf_to_object(f):
    obj = ObjectFile(f.e_machine.aname.lower())
    if f.elf_header.e_entry != 0:
        obj.entry_symbol_id = f.elf_header.e_entry
    
    for s in f.sections:
        so = Section(s.name)
        obj.add_section(so)
        so.address = s.header.sh_addr
        so.data = asc2bin(s.data)
        so.alignment = s.header.sh_addralign if s.header.sh_addralign else 1

    for r in relocations:
        if self.header.r_addend:
            addend = self.header.r_addend)
        else:
            addend = 0
        obj.add_relocation(RelocationEntry(
            r.type,
            r.symbol_id,
            r.section,
            r.header.r_offset,
            addend,
        ))

    if hasattr(f, "symbole_table"):
        for sym in f.symbole_table:
           obj.add_symbol(
                   sym.i,
                   sym.name,
                   SymbolTableBinding(sym.binding).name.lower(),
                   sym.header.st_value,
                   sym.section.name,
                   SymbolTableType(sym.type).name.lower()
                   sym.header.size,
           )
    return obj
