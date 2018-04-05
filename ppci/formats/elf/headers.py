from .. import header


bits = 64
if bits == 32:
    # TODO: create variants for 32 bits:
    SectionHeader = header.mk_header('SectionHeader', [
        header.Uint32('sh_name'),
        header.Uint32('sh_type'),
        header.Uint32('sh_flags'),
        header.Uint32('sh_addr'),
        header.Uint32('sh_offset'),
        header.Uint32('sh_size'),
        header.Uint32('sh_link'),
        header.Uint32('sh_info'),
        header.Uint32('sh_addralign'),
        header.Uint32('sh_entsize'),
    ])
    assert SectionHeader.size == 0x28
else:
    SectionHeader = header.mk_header('SectionHeader', [
        header.Uint32('sh_name'),
        header.Uint32('sh_type'),
        header.Uint64('sh_flags'),
        header.Uint64('sh_addr'),
        header.Uint64('sh_offset'),
        header.Uint64('sh_size'),
        header.Uint32('sh_link'),
        header.Uint32('sh_info'),
        header.Uint64('sh_addralign'),
        header.Uint64('sh_entsize'),
    ])
    assert SectionHeader.size == 0x40

ElfHeader = header.mk_header('ElfHeader', [
    header.Uint16('e_type'),
    header.Uint16('e_machine'),
    header.Uint32('e_version'),
    header.Uint64('e_entry'),
    header.Uint64('e_phoff'),
    header.Uint64('e_shoff'),
    header.Uint32('e_flags'),
    header.Uint16('e_ehsize'),
    header.Uint16('e_phentsize'),
    header.Uint16('e_phnum'),
    header.Uint16('e_shentsize'),
    header.Uint16('e_shnum'),
    header.Uint16('e_shstrndx'),
])
assert ElfHeader.size + 16 == 64

if bits == 64:
    ProgramHeader = header.mk_header('ProgramHeader', [
        header.Uint32('p_type'),
        header.Uint32('p_flags'),
        header.Uint64('p_offset'),
        header.Uint64('p_vaddr'),
        header.Uint64('p_paddr'),
        header.Uint64('p_filesz'),
        header.Uint64('p_memsz'),
        header.Uint64('p_align'),
    ])
    assert ProgramHeader.size == 0x38
else:
    ProgramHeader = header.mk_header('ProgramHeader', [
        header.Uint32('p_type'),
        header.Uint32('p_offset'),
        header.Uint32('p_vaddr'),
        header.Uint32('p_paddr'),
        header.Uint32('p_filesz'),
        header.Uint32('p_memsz'),
        header.Uint32('p_flags'),
        header.Uint32('p_align'),
    ])
    assert ProgramHeader.size == 0x20
