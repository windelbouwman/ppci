"""
 The output stream is a stream of instructions that can be output
 to a file or binary or hexfile.
"""

import logging
from ..arch.isa import Instruction
from ..arch.target import Alignment


class OutputStream:
    """ Interface to generator code with. """
    def emit(self, item):  # pragma: no cover
        """ Encode instruction and add symbol and relocation information """
        raise NotImplementedError('Abstract base class')

    def emit_all(self, items):
        """ Emit an iterable of items """
        for item in items:
            self.emit(item)

    def select_section(self, sname):  # pragma: no cover
        raise NotImplementedError('Abstract base class')


class TextOutputStream(OutputStream):
    """ Output stream that writes to object file """
    def emit(self, item):
        assert isinstance(item, Instruction), str(item) + str(type(item))
        print(item)

    def select_section(self, sname):
        print('section {}'.format(sname))


class BinaryOutputStream(OutputStream):
    """ Output stream that writes to object file """
    def __init__(self, obj_file):
        super().__init__()
        self.obj_file = obj_file
        self.literal_pool = []

    def emit(self, item):
        """ Encode instruction and add symbol and relocation information """
        assert isinstance(item, Instruction), str(item) + str(type(item))
        assert self.currentSection
        section = self.currentSection
        address = self.currentSection.size
        b = item.encode()
        section.add_data(b)
        for sym in item.symbols():
            self.obj_file.add_symbol(sym, address, section.name)
        for sym, typ in item.relocations():
            typ_name = typ.__name__
            self.obj_file.add_relocation(sym, address, typ_name, section.name)

        # Special case for align, TODO do this different?
        if isinstance(item, Alignment):
            while section.size % item.align != 0:
                section.add_data(bytes([0]))
            if item.align > self.currentSection.alignment:
                self.currentSection.alignment = item.align

    def select_section(self, sname):
        self.currentSection = self.obj_file.get_section(sname)


class DummyOutputStream(OutputStream):
    """ Stream that does nothing """
    def emit(self, item):
        pass

    def select_section(self, sname):
        pass


class FunctionOutputStream(OutputStream):
    """ Stream that emits a string to the given function """
    def __init__(self, function):
        self.function = function

    def emit(self, item):
        self.function(str(item))

    def select_section(self, sname):
        self.function('.section {}'.format(sname))


class LoggerOutputStream(FunctionOutputStream):
    """ Stream that emits instructions as text in the log """
    def __init__(self):
        self.logger = logging.getLogger('LoggerOutputStream')
        super().__init__(self.logger.debug)


class MasterOutputStream(OutputStream):
    """ Stream that emits to multiple sub streams """
    def __init__(self, substreams=()):
        self.substreams = list(substreams)   # Use copy constructor!!!

    def emit(self, item):
        for output_stream in self.substreams:
            output_stream.emit(item)

    def select_section(self, sname):
        for output_stream in self.substreams:
            output_stream.select_section(sname)


def binary_and_logging_stream(output):
    """ Create a stream object that both logs and writes to an object file """
    stream1 = BinaryOutputStream(output)
    stream2 = LoggerOutputStream()
    ostream = MasterOutputStream([stream1, stream2])
    return ostream
