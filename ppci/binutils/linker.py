import logging
from .objectfile import ObjectFile, Image
from .. import CompilerError
from .layout import Layout, Section, SymbolDefinition, Align


class Linker:
    """ Merges the sections of several object files and
        performs relocation """
    def __init__(self, target):
        self.logger = logging.getLogger('Linker')
        self.target = target

    def merge_sections(self, objs, dst):
        for iobj in objs:
            offsets = {}
            # Merge sections:
            for in_s in iobj.sections.values():
                out_s = dst.get_section(in_s.name)
                # TODO: align section in other way:
                while out_s.Size % 4 != 0:
                    out_s.add_data(bytes([0]))

                # Add new section:
                offsets[in_s.name] = out_s.Size
                out_s.add_data(in_s.data)
                self.logger.debug('{} {}({})'.format(offsets[in_s.name], iobj, in_s.name))

            # Merge symbols:
            for sym in iobj.symbols.values():
                out_s = dst.get_section(sym.section)
                value = offsets[sym.section] + sym.value
                dst.add_symbol(sym.name, value, sym.section)
                # self.logger.debug('{} at 0x{:08X} in section {}'
                # .format(sym.name, value, sym.section))

            # Merge relocations:
            for reloc in iobj.relocations:
                offset = offsets[reloc.section] + reloc.offset
                dst.add_relocation(reloc.sym, offset, reloc.typ, reloc.section)

    def layout_sections(self, dst, layout):
        """ Use the given layout to place sections into memories """
        # Create sections with address:
        dst.images = {}
        for mem in layout.memories:
            image = Image(mem.location)
            cur_addr = mem.location
            output_memory = bytearray()
            for memory_input in mem.inputs:
                if type(memory_input) is Section:
                    section = dst.get_section(memory_input.section_name)
                    section.address = cur_addr
                    self.logger.debug(
                        'Memory: {} Section: {} Address: 0x{:X} Size: 0x{:X}'
                        .format(mem.name, section.name,
                                section.address, section.Size))
                    cur_addr += section.Size
                    output_memory += section.data
                    # TODO: align sections
                elif type(memory_input) is SymbolDefinition:
                    dst.add_symbol(memory_input.symbol_name, cur_addr, "code")
                elif type(memory_input) is Align:
                    while (cur_addr % memory_input.alignment) != 0:
                        cur_addr += 1
                        output_memory += bytes([0])
                else:
                    raise NotImplementedError(str(memory_input))
            # Check that the memory fits!
            image.data = bytes(output_memory)
            if image.size > mem.size:
                raise CompilerError(
                    'Memory exceeds size ({} > {})'
                    .format(image.size, mem.size))
            dst.images[mem.name] = image

    def do_relocations(self, dst):
        """ Perform the correct relocation as listed """
        for reloc in dst.relocations:
            # Lookup symbol:
            if reloc.sym not in dst.symbols:
                raise CompilerError(
                    'Undefined reference "{}"'.format(reloc.sym))

            sym_value = dst.get_symbol_value(reloc.sym)
            section = dst.get_section(reloc.section)

            # Determine location in memory of reloc patchup position:
            reloc_value = section.address + reloc.offset

            if reloc.typ in self.target.reloc_map:
                f = self.target.reloc_map[reloc.typ]
                f(reloc, sym_value, section, reloc_value)
            else:
                raise NotImplementedError(
                    'Unknown relocation type {}'.format(reloc.typ))

    def link(self, objs, layout):
        """ Link together the given object files using the layout """
        assert type(objs) is list
        assert type(layout) is Layout
        # Create new object file to store output:
        dst = ObjectFile()

        # First merge all sections into output sections:
        self.merge_sections(objs, dst)

        # Apply layout rules:
        self.layout_sections(dst, layout)

        # Perform relocations:
        self.do_relocations(dst)

        # Create memories for the second time
        # TODO: make this nicer?
        self.layout_sections(dst, layout)

        return dst
