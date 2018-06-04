""" Linker utility. """

import logging
from .objectfile import ObjectFile, Image, get_object
from ..common import CompilerError
from .layout import Layout, Section, SectionData, SymbolDefinition, Align
from .layout import get_layout
from .debuginfo import SectionAdjustingReplicator, DebugInfo


def link(
        objects, layout=None, use_runtime=False, partial_link=False,
        reporter=None, debug=False, extra_symbols=None):
    """ Links the iterable of objects into one using the given layout.

    Args:
        objects: a collection of objects to be linked together.
        use_runtime (bool): also link compiler runtime functions
        debug (bool): when true, keep debug information. Otherwise remove
            this debug information from the result.

    Returns:
        The linked object file

    .. doctest::

        >>> import io
        >>> from ppci.api import asm, c3c, link
        >>> asm_source = io.StringIO("db 0x77")
        >>> obj1 = asm(asm_source, 'arm')
        >>> c3_source = io.StringIO("module main; var int a;")
        >>> obj2 = c3c([c3_source], [], 'arm')
        >>> obj = link([obj1, obj2])
        >>> print(obj)
        CodeObject of 8 bytes
    """

    objects = [get_object(obj) for obj in objects]
    if not objects:
        raise ValueError('Please provide at least one object as input')

    if layout:
        layout = get_layout(layout)

    march = objects[0].arch

    if use_runtime:
        objects.append(march.runtime)

    linker = Linker(march, reporter)
    output_obj = linker.link(
        objects, layout=layout, partial_link=partial_link,
        debug=debug, extra_symbols=extra_symbols)
    return output_obj


class Linker:
    """ Merges the sections of several object files and
        performs relocation """
    logger = logging.getLogger('linker')

    def __init__(self, arch, reporter=None):
        self.arch = arch
        self.reporter = reporter

    def link(self, input_objects, layout=None, partial_link=False,
             debug=False, extra_symbols=None):
        """ Link together the given object files using the layout """
        assert isinstance(input_objects, (list, tuple))

        if self.reporter:
            self.reporter.heading(2, 'Linking')

        if extra_symbols:
            self.extra_symbols = extra_symbols
        else:
            self.extra_symbols = {}

        # Check all incoming objects for same architecture:
        for input_object in input_objects:
            assert input_object.arch == self.arch

        # Create new object file to store output:
        dst = ObjectFile(self.arch)
        if debug:
            dst.debug_info = DebugInfo()

        # First merge all sections into output sections:
        self.merge_objects(input_objects, dst, debug)

        # Apply layout rules:
        if layout:
            assert isinstance(layout, Layout)
            self.layout_sections(dst, layout)

        if not partial_link:
            self.do_relocations(dst)
        
        for func in dst.arch.isa.postlinkopts:
            func(self, dst)

        if self.reporter:
            for section in dst.sections:
                self.reporter.message(
                    '{} at {}'.format(section, section.address))
            for image in dst.images:
                self.reporter.message(
                    '{} at {}'.format(image, image.address))
            symbols = [
                (s.name, dst.get_symbol_value(s.name)) for s in dst.symbols]
            symbols.sort(key=lambda x: x[1])
            for name, address in symbols:
                self.reporter.message(
                    'Symbol {} at 0x{:X}'.format(name, address))
        dst.polish()

        if self.reporter:
            self.reporter.message('Linking complete')
        return dst

    def merge_objects(self, input_objects, dst, debug):
        """ Merge object files into a single object file """
        for input_object in input_objects:
            self.logger.debug('Merging %s', input_object)
            offsets = {}
            # Merge sections:
            for input_section in input_object.sections:
                # Get or create the output section:
                output_section = dst.get_section(
                    input_section.name, create=True)

                # Align section:
                while output_section.size % input_section.alignment != 0:
                    self.logger.debug('Padding output to ensure alignment')
                    output_section.add_data(bytes([0]))

                # Alter the output section alignment if required:
                if input_section.alignment > output_section.alignment:
                    output_section.alignment = input_section.alignment

                # Add new section:
                offset = output_section.size
                offsets[input_section.name] = offset
                output_section.add_data(input_section.data)
                self.logger.debug(
                    'at offset 0x%x section %s',
                    offsets[input_section.name],
                    input_section)

            # Merge symbols:
            for sym in input_object.symbols:
                value = offsets[sym.section] + sym.value
                dst.add_symbol(sym.name, value, sym.section)

            # Merge relocations:
            for reloc in input_object.relocations:
                offset = offsets[reloc.section] + reloc.offset
                new_reloc = type(reloc)(
                    reloc.symbol_name, section=reloc.section, offset=offset,
                    addend=reloc.addend)
                dst.add_relocation(new_reloc)

            # Merge debug info:
            if debug and input_object.debug_info:
                replicator = SectionAdjustingReplicator(offsets)
                replicator.replicate(input_object.debug_info, dst.debug_info)

    def layout_sections(self, dst, layout):
        """ Use the given layout to place sections into memories """
        # Create sections with address:
        for mem in layout.memories:
            image = Image(mem.name, mem.location)
            current_address = mem.location
            for memory_input in mem.inputs:
                if isinstance(memory_input, Section):
                    section = dst.get_section(
                        memory_input.section_name, create=True)
                    while current_address % section.alignment != 0:
                        current_address += 1
                    section.address = current_address
                    self.logger.debug(
                        'Memory: %s Section: %s Address: 0x%x Size: 0x%x',
                        mem.name, section.name,
                        section.address, section.size)
                    current_address += section.size
                    image.add_section(section)
                elif isinstance(memory_input, SectionData):
                    section_name = '_${}_'.format(memory_input.section_name)
                    # Each section must be unique:
                    assert not dst.has_section(section_name)

                    section = dst.get_section(section_name, create=True)
                    section.address = current_address
                    section.alignment = 1  # TODO: is this correct alignment?

                    src_section = dst.get_section(memory_input.section_name)

                    section.add_data(src_section.data)

                    current_address += section.size
                    image.add_section(section)
                elif isinstance(memory_input, SymbolDefinition):
                    # Create a new section, and place it at current spot:
                    section_name = '_${}_'.format(memory_input.symbol_name)

                    # Each section must be unique:
                    assert not dst.has_section(section_name)

                    section = dst.get_section(section_name, create=True)
                    section.address = current_address
                    section.alignment = 1
                    dst.add_symbol(memory_input.symbol_name, 0, section_name)
                    image.add_section(section)
                elif isinstance(memory_input, Align):
                    while (current_address % memory_input.alignment) != 0:
                        current_address += 1
                else:  # pragma: no cover
                    raise NotImplementedError(str(memory_input))

            # Check that the memory fits!
            if image.size > mem.size:
                raise CompilerError(
                    'Memory exceeds size ({} > {})'
                    .format(image.size, mem.size))
            dst.add_image(image)

    def get_symbol_value(self, obj, name):
        """ Get value of a symbol from object or fallback """
        # Lookup symbol:
        if obj.has_symbol(name):
            return obj.get_symbol_value(name)
        elif name in self.extra_symbols:
            return self.extra_symbols[name]
        else:
            raise CompilerError(
                'Undefined reference "{}"'.format(name))

    def do_relocations(self, dst, opt = False):
        """ Perform the correct relocation as listed """
        for reloc in dst.relocations:
            sym_value = self.get_symbol_value(dst, reloc.symbol_name)
            section = dst.get_section(reloc.section)

            # Determine address in memory of reloc patchup position:
            reloc_value = section.address + reloc.offset

            # reloc_function = self.arch.get_reloc(reloc.typ)
            begin = reloc.offset
            size = reloc.size()
            end = begin + size
            data = section.data[begin:end]
            if opt:
                data, size = reloc.apply(sym_value, data, reloc_value, opt)
                end = begin + size
                data = data[0:size]
            else:
                assert len(data) == size, \
                'len({}) ({}-{}) != {}'.format(data, begin, end, size)
                data = reloc.apply(sym_value, data, reloc_value)
            assert len(data) == size
            section.data[begin:end] = data
            
            
