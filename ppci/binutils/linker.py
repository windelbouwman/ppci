""" Linker utility. """

import logging
from collections import defaultdict
from .objectfile import ObjectFile, Image, get_object, RelocationEntry
from ..common import CompilerError
from .layout import Layout, Section, SectionData, SymbolDefinition, Align
from .layout import get_layout
from .debuginfo import SymbolIdAdjustingReplicator, DebugInfo
from .archive import get_archive


def link(
    objects,
    layout=None,
    use_runtime=False,
    partial_link=False,
    reporter=None,
    debug=False,
    extra_symbols=None,
    libraries=None,
    entry=None,
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
        libraries: a list of libraries to use when searching for symbols.
        entry: the entry symbol where execution should begin.

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

    objects = list(map(get_object, objects))
    if not objects:
        raise ValueError("Please provide at least one object as input")

    if layout:
        layout = get_layout(layout)

    march = objects[0].arch

    if use_runtime:
        objects.append(march.runtime)

    libraries = list(map(get_archive, libraries)) if libraries else []

    linker = Linker(march, reporter)
    output_obj = linker.link(
        objects,
        layout=layout,
        partial_link=partial_link,
        debug=debug,
        extra_symbols=extra_symbols,
        libraries=libraries,
        entry_symbol_name=entry,
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
        libraries=None,
        entry_symbol_name=None,
    ):
        """ Link together the given object files using the layout """
        assert isinstance(input_objects, (list, tuple))

        if self.reporter:
            self.reporter.heading(2, "Linking")

        # Check all incoming objects for same architecture:
        for input_object in input_objects:
            assert input_object.arch == self.arch

        # Create new object file to store output:
        self.dst = ObjectFile(self.arch)
        if debug:
            self.dst.debug_info = DebugInfo()

        # Take entry symbol from layout if not specified alreay:
        if not entry_symbol_name and layout and layout.entry:
            # TODO: what to do if two symbols are defined?
            # for now the symbol given via command line overrides
            # the entry in the linker script.
            entry_symbol_name = layout.entry.symbol_name

        # Define entry symbol:
        if entry_symbol_name:
            self.dst.entry_symbol_id = self.inject_symbol(
                entry_symbol_name, "global", None, None, 'object', 0
            ).id

        # Define extra symbols:
        extra_symbols = extra_symbols or {}
        for symbol_name, value in extra_symbols.items():
            self.logger.debug("Defining extra symbol %s", symbol_name)
            self.inject_symbol(symbol_name, "global", None, value, 'object', 0)

        # First merge all sections into output sections:
        self.merge_objects(input_objects, debug)

        if partial_link:
            if layout:
                # Layout makes only sense in the final binary.
                raise ValueError("Can only apply layout in non-partial links")
        else:
            if libraries:
                # Find missing symbols in libraries:
                self.add_missing_symbols_from_libraries(libraries)

            # Apply layout rules:
            if layout:
                assert isinstance(layout, Layout)
                self.layout_sections(layout)

            self.check_undefined_symbols()

            self.do_relaxations()
            self.do_relocations()

        if self.reporter:
            self.report_link_result()

        return self.dst

    def report_link_result(self):
        """ After linking is complete, this function can be used to dump
        information to a reporter.
        """
        for section in self.dst.sections:
            self.reporter.message("{} at {}".format(section, section.address))

        for image in self.dst.images:
            self.reporter.message("{} at {}".format(image, image.address))

        symbols = [
            (s, self.dst.get_symbol_id_value(s.id) if s.defined else -1)
            for s in self.dst.symbols
        ]
        symbols.sort(key=lambda x: x[1])
        for symbol, address in symbols:
            self.reporter.message(
                "Symbol {} {} at 0x{:X}".format(
                    symbol.binding, symbol.name, address
                )
            )

        self.reporter.message("Linking complete")

    def merge_objects(self, input_objects, debug):
        """ Merge object files into a single object file """

        for input_object in input_objects:
            self.inject_object(input_object, debug)

    def inject_object(self, obj, debug):
        """ Paste object into destination object. """
        self.logger.debug("Merging %s", obj)

        section_offsets = {}
        for input_section in obj.sections:
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
        for symbol in obj.symbols:
            # Shift symbol value if required:
            if symbol.defined:
                value = section_offsets[symbol.section] + symbol.value
                section = symbol.section
            else:
                value = section = None

            if symbol.binding == "global":
                new_symbol = self.merge_global_symbol(
                    symbol.name, section, value, symbol.typ, symbol.size
                )
            else:
                new_symbol = self.inject_symbol(
                    symbol.name, symbol.binding, section, value, symbol.typ, symbol.size
                )

            symbol_id_mapping[symbol.id] = new_symbol.id

        for reloc in obj.relocations:
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

        # Merge entry symbol:
        if obj.entry_symbol_id is not None:
            if self.dst.entry_symbol_id is None:
                self.dst.entry_symbol_id = symbol_id_mapping[
                    obj.entry_symbol_id
                ]
            else:
                # TODO: improve error message?
                raise CompilerError("Multiple entry points defined")

        # Merge debug info:
        if debug and obj.debug_info:
            replicator = SymbolIdAdjustingReplicator(symbol_id_mapping)
            replicator.replicate(obj.debug_info, self.dst.debug_info)

    def merge_global_symbol(self, name, section, value, typ, size):
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
            new_symbol = self.inject_symbol(name, "global", section, value, typ, size)

        return new_symbol

    def inject_symbol(self, name, binding, section, value, typ, size):
        """ Generate new symbol into object file. """
        symbol_id = len(self.dst.symbols)
        new_symbol = self.dst.add_symbol(
            symbol_id, name, binding, value, section, typ, size
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
                    self.merge_global_symbol(symbol_name, section_name, 0, 'object', 0)
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

    def get_symbol_value(self, symbol_id):
        """ Get value of a symbol from object or fallback """
        # Lookup symbol:
        return self.dst.get_symbol_id_value(symbol_id)
        #    raise CompilerError('Undefined reference "{}"'.format(name))

    def add_missing_symbols_from_libraries(self, libraries):
        """ Try to fetch extra code from libraries to resolve symbols.

        Note that this can be a rabbit hole, since libraries can have undefined
        symbols as well.
        """
        undefined_symbols = self.get_undefined_symbols()
        if not undefined_symbols:
            self.logger.debug(
                "No undefined symbols, no need to check libraries"
            )
            return

        # Keep adding objects while we have undefined symbols.
        reloop = True
        while reloop:
            reloop = False
            for library in libraries:
                self.logger.debug("scanning library for symbols %s", library)
                for obj in library:
                    has_sym = any(map(obj.has_symbol, undefined_symbols))
                    if has_sym:
                        self.logger.debug(
                            "Using object file %s from library", obj
                        )
                        self.inject_object(obj, False)
                        undefined_symbols = self.get_undefined_symbols()
                        reloop = True

    def get_undefined_symbols(self):
        """ Get a list of currently undefined symbols.
        """
        return self.dst.get_undefined_symbols()

    def check_undefined_symbols(self):
        """ Find undefined symbols.
        """
        undefined_symbols = self.get_undefined_symbols()
        for symbol in undefined_symbols:
            self.logger.error("Undefined reference: %s", symbol)

        if undefined_symbols:
            undefined = ", ".join(undefined_symbols)
            raise CompilerError("Undefined references: {}".format(undefined))

    def do_relaxations(self):
        """ Linker relaxation. Just relax ;).

        Linker relaxation is the process of finding shorted opcodes for
        jumps to addresses nearby.

        For example, an instruction set might
        define two jump operations. One with a 32 bits offset, and one with
        an 8 bits offset. Most likely the compiler will generate conservative
        code, so always 32 bits branches. During the relaxation phase, the
        code is scanned for possible replacements of the 32 bits jump by an
        8 bit jump.

        Possible issues that might occur during this phase:

        - alignment of code. Code that was previously aligned might be
          shifted.

        - Linker relaxations might cause the opposite effect on jumps whose
          distance increases due to relaxation. This occurs when jumping over
          a memory whole between sections.

        """

        self.logger.debug("Doing linker relaxations")

        # TODO: general note. Alignment must still be taken into account.
        # A wrong situation occurs, when reducing the image by small amount
        # of bytes. Locations that were aligned before, might become unaligned.

        # First, determine the list of possible optimizations!
        lst = []
        for relocation in self.dst.relocations:
            sym_value = self.get_symbol_value(relocation.symbol_id)
            reloc_section = self.dst.get_section(relocation.section)
            reloc_value = reloc_section.address + relocation.offset
            rcls = self.dst.arch.isa.relocation_map[relocation.reloc_type]
            reloc = rcls(
                None, offset=relocation.offset, addend=relocation.addend
            )
            if reloc.can_shrink(sym_value, reloc_value):
                # Apply code patching:
                begin = relocation.offset
                size = reloc.size()
                end = begin + size
                data = reloc_section.data[begin:end]
                assert len(data) == size, "len({}) ({}-{}) != {}".format(
                    data, begin, end, size
                )

                # Apply code patch:
                self.logger.debug("Applying patch for %s", reloc)
                data, new_relocs = reloc.do_shrink(
                    sym_value, data, reloc_value
                )
                new_size = len(data)
                diff = size - new_size
                assert 0 <= diff <= size
                # assert len(data) == size
                new_end = begin + new_size
                assert new_end + new_size == end
                # Do not shrink the data here, we will do this later on.
                reloc_section.data[begin:new_end] = data

                # Define new memory hole, starting after instruction
                hole = (new_end, diff)

                # Record this reduction occurence:
                lst.append((hole, relocation, reloc, new_relocs))

        if not lst:
            self.logger.debug("No linker relaxations found")
            return

        s = ", ".join(str(x) for x in lst)
        self.logger.debug("Relaxable relocations: %s", s)

        # Define a map with the byte holes:
        holes_map = defaultdict(list)  # section name to list of holes.

        # Remove old relocations by new ones.
        for hole, relocation, reloc, new_relocs in lst:
            # Remove old relocation which is superceeded:
            self.dst.relocations.remove(relocation)

            # Inject new relocations:
            for new_reloc in new_relocs:
                # TODO: maybe deal with somewhat shifted new relocations?

                # Create fresh relocation entry for patched code.
                new_relocation = RelocationEntry(
                    new_reloc.name,
                    relocation.symbol_id,
                    relocation.section,
                    relocation.offset,
                    relocation.addend,
                )
                self.dst.add_relocation(new_relocation)

            # Register hole:
            assert relocation.section
            holes_map[relocation.section].append(hole)

        for holes in holes_map.values():
            holes.sort(key=lambda x: x[0])

        # TODO: at this point, there can be the situation that we have two
        # sections which become further apart (due to them being in different
        # memory images. In this case, some relative jumps can become
        # unreachable. What should be do in this case?

        # Code has been patched here. Now update all relocations, symbols and
        # section addresses.
        self._apply_relaxation_holes(holes_map)

    def _apply_relaxation_holes(self, hole_map):
        """ Punch holes in the destination object file.

        Do adjustments to section addresses, symbol offsets
        and relocation offsets.
        """

        def count_holes(offset, holes):
            """ Count how much holes we have until the given offset. """
            diff = 0
            for hole_offset, hole_size in holes:
                if hole_offset < offset:
                    diff += hole_size
                else:
                    break
            return diff

        # Update symbols which are located in sections.
        for symbol in self.dst.symbols:
            # Ignore global section-less symbols.
            if symbol.section is None:
                continue
            holes = hole_map[symbol.section]
            delta = count_holes(symbol.value, holes)
            self.logger.debug(
                "symbol changing %s (id=%s) at %08x with -%08x",
                symbol.name,
                symbol.id,
                symbol.value,
                delta,
            )
            symbol.value -= delta

        # Update relocations (which are always located in a section)
        for relocation in self.dst.relocations:
            assert relocation.section
            holes = hole_map[relocation.section]
            delta = count_holes(relocation.offset, holes)
            self.logger.debug(
                "relocation changing %s at offset %08x with -%08x",
                relocation.symbol_id,
                relocation.offset,
                delta,
            )
            relocation.offset -= delta

        # Update section data:
        for section in self.dst.sections:
            # Loop over holes in reverse, since earlier holes influence later
            # holes.
            holes = hole_map[section.name]
            for hole_offset, hole_size in reversed(holes):
                for _ in range(hole_size):
                    section.data.pop(hole_offset)

        # Calculate total change per section
        section_changes = {
            name: sum(h[1] for h in holes) for name, holes in hole_map.items()
        }

        # Update layout of section in images
        for image in self.dst.images:
            delta = 0
            for section in image.sections:
                self.logger.debug(
                    "sectororchanging %s at %08x with -%08x to %08x",
                    section.name,
                    section.address,
                    delta,
                )
                # TODO: tricky stuff might go wrong here with alignment
                # requirements of sections.
                # Idea: re-do the layout phase?
                section.address -= delta
                delta += section_changes[section.name]

    def do_relocations(self):
        """ Perform the correct relocation as listed """
        self.logger.debug(
            "Performing {} linker relocations".format(
                len(self.dst.relocations)
            )
        )
        for reloc in self.dst.relocations:
            self._do_relocation(reloc)

    def _do_relocation(self, relocation):
        """ Perform a single relocation.

        This involves hammering some specific bits in the section data
        according to symbol location and relocation location in the file.
        """
        sym_value = self.get_symbol_value(relocation.symbol_id)
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
        assert len(data) == size, "len({}) ({}-{}) != {}".format(
            data, begin, end, size
        )
        data = reloc.apply(sym_value, data, reloc_value)
        assert len(data) == size
        section.data[begin:end] = data
