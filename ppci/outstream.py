import logging
import binascii
from .target import Instruction, Alignment
from .objectfile import ObjectFile

"""
 The output stream is a stream of instructions that can be output
 to a file or binary or hexfile.
"""


class OutputStream:
    """ Interface to generator code with. """
    def emit(self, item):
        raise NotImplementedError('Abstract base class')

    def select_section(self, sname):
        raise NotImplementedError('Abstract base class')


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
        address = self.currentSection.Size
        b = item.encode()
        syms = item.symbols()
        relocs = item.relocations()
        section.add_data(b)
        for sym in syms:
            self.obj_file.add_symbol(sym, address, section.name)
        for sym, typ in relocs:
            self.obj_file.add_relocation(sym, address, typ, section.name)
        # Special case for align, TODO do this different?
        if type(item) is Alignment:
            while section.Size % item.align != 0:
                section.add_data(bytes([0]))

    def select_section(self, sname):
        self.currentSection = self.obj_file.get_section(sname)


class DummyOutputStream(OutputStream):
    """ Stream that implements the bare minimum and does nothing """
    def emit(self, item):
        pass

    def select_section(self, sname):
        pass


class LoggerOutputStream(OutputStream):
    """ Stream that emits instructions as text in the log """
    def __init__(self):
        self.logger = logging.getLogger('LoggerOutputStream')

    def emit(self, item):
        self.logger.debug(str(item))

    def select_section(self, sname):
        self.logger.debug('.section {}'.format(sname))


class MasterOutputStream(OutputStream):
    """ Stream that emits to multiple sub streams """
    def __init__(self, substreams=[]):
        self.substreams = list(substreams)  # Use copy constructor!!!

    def add_substream(self, output_stream):
        self.substreams.append(output_stream)

    def emit(self, item):
        for output_stream in self.substreams:
            output_stream.emit(item)

    def select_section(self, sname):
        for output_stream in self.substreams:
            output_stream.select_section(sname)


def BinaryAndLoggingStream(output):
    """ Create a stream object that both logs and writes to an object file """
    o2 = BinaryOutputStream(output)
    o1 = LoggerOutputStream()
    ostream = MasterOutputStream([o1, o2])
    return ostream
