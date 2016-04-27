"""
 The output stream is a stream of instructions that can be output
 to a file or binary or hexfile.
"""

import logging
from ..arch.isa import Instruction
from ..arch.arch import Alignment, DebugData


class OutputStream:
    """ Interface to generate code with. Contains the emit function to output
    instruction to the stream """
    def emit(self, item):  # pragma: no cover
        """ Encode instruction and add symbol and relocation information """
        raise NotImplementedError('Abstract base class')

    def emit_all(self, items):
        """ Emit all items from an iterable """
        for item in items:
            self.emit(item)

    def select_section(self, sname):  # pragma: no cover
        """ Switch stream into another section """
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
        self.current_section = None

    def emit(self, item):
        """ Encode instruction and add symbol and relocation information.
            At this point we know the address of the instruction.
        """
        assert isinstance(item, Instruction), str(item) + str(type(item))
        assert self.current_section
        section = self.current_section
        address = self.current_section.size
        bin_data = item.encode()
        section.add_data(bin_data)
        for sym in item.symbols():
            self.obj_file.add_symbol(sym, address, section.name)
        for sym, typ in item.relocations():
            typ_name = typ.__name__
            self.obj_file.add_relocation(sym, address, typ_name, section.name)

        # Special case for align, TODO do this different?
        if isinstance(item, Alignment):
            while section.size % item.align != 0:
                section.add_data(bytes([0]))
            if item.align > self.current_section.alignment:
                self.current_section.alignment = item.align
        elif isinstance(item, DebugData):
            # We have debug data here!
            self.obj_file.debug_info.add(item.data)

    def select_section(self, sname):
        self.current_section = self.obj_file.get_section(sname, create=True)


class RecordingOutputStream(OutputStream):
    """ Stream that appends instructions to list """
    def __init__(self, bag):
        self.bag = bag

    def emit(self, item):
        self.bag.append(item)

    def select_section(self, sname):
        pass


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
