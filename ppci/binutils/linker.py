""" Linker utility. """

import logging
from .objectfile import ObjectFile, Image, get_object, RelocationEntry
from ..common import CompilerError
from .layout import Layout, Section, SectionData, SymbolDefinition, Align
from .layout import get_layout
from .debuginfo import SymbolIdAdjustingReplicator, DebugInfo


def link(
    objects,
    layout=None,
    use_runtime=False,
    partial_link=False,
    reporter=None,
    debug=False,
    extra_symbols=None,
):
    """ Links the iterable of objects into one using the given layout.

    Args:
        objects: a collection of objects to be linked together.
        layout: optional memory layout.
        use_runtime (bool): also link compiler runtime functions
        partial_link: Set this to true if you want to perform a partial link.
            This means, undefined symbols are no error.
        debug (bool): when true, keep debug information. Otherwise remove
            this debug information from the result.
        extra_symbols: a dict of extra symbols which can be used during
            linking.

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
        raise ValueError("Please provide at least one object as input")

    if layout:
        layout = get_layout(layout)

    march = objects[0].arch

    if use_runtime:
        objects.append(march.runtime)

    linker = Linker(march, reporter)
    output_obj = linker.link(
        objects,
        layout=layout,
        partial_link=partial_link,
        debug=debug,
        extra_symbols=extra_symbols,
    )
    return output_obj


class Linker:
    """ Merges the sections of several object files and
        performs relocation """

    logger = logging.getLogger("linker")

    def __init__(self, arch, reporter=None):
        self.arch = arch
        self.extra_symbols = None
        self.reporter = reporter

    def link(
        self,
        input_objects,
        layout=None,
        partial_link=False,
        debug=False,
        extra_symbols=None,
    ):
        """ Link together the given object files using the layout """
        assert isinstance(input_objects, (list, tuple))

        if self.reporter:
            self.reporter.heading(2, "Linking")

        # Check all incoming objects for same architecture:
        for input_object in input_objects:
            assert input_object.arch == self.arch

        # Create new object file to store output:
        dst = ObjectFile(self.arch)
        self.dst = dst
        if debug:
            dst.debug_info = DebugInfo()

        # Define extra symbols:
        extra_symbols = extra_symbols or {}
        for symbol_name, value in extra_symbols.items():
            self.logger.debug("Defining extra symbol %s", symbol_name)
            self.inject_symbol(symbol_name, "global", None, value)

        # First merge all sections into output sections:
        self.merge_objects(input_objects, debug)

        # Apply layout rules:
        if layout:
            assert isinstance(layout, Layout)
            self.layout_sections(layout)

        if not partial_link:
            self.do_relocations()

        for func in dst.arch.isa.postlinkopts:
            func(self, dst)

        if self.reporter:
            for section in dst.sections:
                self.reporter.message(
                    "{} at {}".format(section, section.address)
                )

            for image in dst.images:
                self.reporter.message("{} at {}".format(image, image.address))

            symbols = [
                (s, dst.get_symbol_id_value(s.id) if s.defined else -1)
                for s in dst.symbols
            ]
            symbols.sort(key=lambda x: x[1])
            for symbol, address in symbols:
                self.reporter.message(
                    "Symbol {} {} at 0x{:X}".format(
                        symbol.binding, symbol.name, address
                    )
                )

        if self.reporter:
            self.reporter.message("Linking complete")
        return dst

    def merge_objects(self, input_objects, debug):
        """ Merge object files into a single object file """

        for input_object in input_objects:
            self.logger.debug("Merging %s", input_object)
            section_offsets = {}

            for input_section in input_object.sections:
                # Get or create the output section:
                output_section = self.dst.get_section(
                    input_section.name, create=True
                )

                # Alter the minimum section alignment if required:
                if input_section.alignment > output_section.alignment:
                    output_section.alignment = input_section.alignment

                # Align section:
                while output_section.size % input_section.alignment != 0:
                    self.logger.debug("Padding output to ensure alignment")
                    output_section.add_data(bytes([0]))

                # Add new section:
                offset = output_section.size
                section_offsets[input_section.name] = offset
                output_section.add_data(input_section.data)
                self.logger.debug(
                    "at offset 0x%x section %s",
                    section_offsets[input_section.name],
                    input_section,
                )

            symbol_id_mapping = {}
            for symbol in input_object.symbols:
                # Shift symbol value if required:
                if symbol.defined:
                    value = section_offsets[symbol.section] + symbol.value
                    section = symbol.section
                else:
                    value = section = None

                if symbol.binding == "global":
                    new_symbol = self.merge_global_symbol(
                        symbol.name, section, value
                    )
                else:
                    new_symbol = self.inject_symbol(
                        symbol.name, symbol.binding, section, value
                    )

                symbol_id_mapping[symbol.id] = new_symbol.id

            for reloc in input_object.relocations:
                offset = section_offsets[reloc.section] + reloc.offset
                symbol_id = symbol_id_mapping[reloc.symbol_id]
                new_reloc = RelocationEntry(
                    reloc.reloc_type,
                    symbol_id,
                    reloc.section,
                    offset,
                    reloc.addend,
                )
                self.dst.add_relocation(new_reloc)

            # Merge debug info:
            if debug and input_object.debug_info:
                replicator = SymbolIdAdjustingReplicator(symbol_id_mapping)
                replicator.replicate(
                    input_object.debug_info, self.dst.debug_info
                )

    def merge_global_symbol(self, name, section, value):
        """ Insert or merge a global name. """
        if self.dst.has_symbol(name):
            new_symbol = self.dst.get_symbol(name)
            assert new_symbol.binding == "global"
            if value is not None:  # we define this symbol.
                # We require merging.
                if new_symbol.undefined:
                    new_symbol.value = value
                    new_symbol.section = section
                else:
                    # TODO: accumulate errors..
                    raise CompilerError(
                        "Multiple defined symbol: {}".format(name)
                    )
        else:
            new_symbol = self.inject_symbol(name, "global", section, value)

        return new_symbol

    def inject_symbol(self, name, binding, section, value):
        """ Generate new symbol into object file. """
        symbol_id = len(self.dst.symbols)
        new_symbol = self.dst.add_symbol(
            symbol_id, name, binding, value, section
        )
        return new_symbol

    def layout_sections(self, layout):
        """ Use the given layout to place sections into memories """
        # Create sections with address:
        for mem in layout.memories:
            image = Image(mem.name, mem.location)
            current_address = mem.location
            for memory_input in mem.inputs:
                if isinstance(memory_input, Section):
                    section = self.dst.get_section(
                        memory_input.section_name, create=True
                    )
                    while current_address % section.alignment != 0:
                        current_address += 1
                    section.address = current_address
                    self.logger.debug(
                        "Memory: %s Section: %s Address: 0x%x Size: 0x%x",
                        mem.name,
                        section.name,
                        section.address,
                        section.size,
                    )
                    current_address += section.size
                    image.add_section(section)
                elif isinstance(memory_input, SectionData):
                    section_name = "_${}_".format(memory_input.section_name)
                    # Each section must be unique:
                    assert not self.dst.has_section(section_name)

                    section = self.dst.get_section(section_name, create=True)
                    section.address = current_address
                    section.alignment = 1  # TODO: is this correct alignment?

                    src_section = self.dst.get_section(
                        memory_input.section_name
                    )

                    section.add_data(src_section.data)

                    current_address += section.size
                    image.add_section(section)
                elif isinstance(memory_input, SymbolDefinition):
                    # Create a new section, and place it at current spot:
                    symbol_name = memory_input.symbol_name
                    section_name = "_${}_".format(symbol_name)

                    # Each section must be unique:
                    assert not self.dst.has_section(section_name)

                    section = self.dst.get_section(section_name, create=True)
                    section.address = current_address
                    section.alignment = 1
                    self.merge_global_symbol(symbol_name, section_name, 0)
                    image.add_section(section)
                elif isinstance(memory_input, Align):
                    while (current_address % memory_input.alignment) != 0:
                        current_address += 1
                else:  # pragma: no cover
                    raise NotImplementedError(str(memory_input))

            # Check that the memory fits!
            if image.size > mem.size:
                raise CompilerError(
                    "Memory exceeds size ({} > {})".format(
                        image.size, mem.size
                    )
                )
            self.dst.add_image(image)

    def get_symbol_value(self, obj, symbol_id):
        """ Get value of a symbol from object or fallback """
        # Lookup symbol:
        return obj.get_symbol_id_value(symbol_id)
        #    raise CompilerError('Undefined reference "{}"'.format(name))

    def do_relocations(self, opt=False):
        """ Perform the correct relocation as listed """
        # Check undefined symbols:
        self._check_undefined_symbols()

        for reloc in self.dst.relocations:
            self._do_relocation(reloc, opt=opt)

    def _check_undefined_symbols(self):
        undefined_symbols = []
        for symbol in self.dst.symbols:
            if symbol.undefined:
                self.logger.error("Undefined reference: %s", symbol.name)
                undefined_symbols.append(symbol.name)

        if undefined_symbols:
            raise CompilerError(
                "Undefined references: {}".format(
                    ", ".join(str(s) for s in undefined_symbols)
                )
            )

    def _do_relocation(self, relocation, opt=False):
        """ Perform a single relocation. """
        sym_value = self.get_symbol_value(self.dst, relocation.symbol_id)
        section = self.dst.get_section(relocation.section)

        # Determine address in memory of reloc patchup position:
        reloc_value = section.address + relocation.offset

        # reloc_function = self.arch.get_reloc(reloc.typ)
        # Construct architecture specific relocation:
        rcls = self.dst.arch.isa.relocation_map[relocation.reloc_type]
        reloc = rcls(None, offset=relocation.offset, addend=relocation.addend)

        begin = relocation.offset
        size = reloc.size()
        end = begin + size
        data = section.data[begin:end]
        if opt:
            data, size = reloc.apply(sym_value, data, reloc_value, opt)
            end = begin + size
            data = data[0:size]
        else:
            assert len(data) == size, "len({}) ({}-{}) != {}".format(
                data, begin, end, size
            )
            data = reloc.apply(sym_value, data, reloc_value)
        assert len(data) == size
        section.data[begin:end] = data
