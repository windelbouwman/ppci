"""
 The output stream is a stream of instructions that can be output
 to a file or binary or hexfile.
"""

import logging
import abc
import binascii
from ..arch.encoding import Instruction
from ..arch.asm_printer import AsmPrinter
from ..arch.generic_instructions import Alignment, DebugData, Label
from ..arch.generic_instructions import SectionInstruction
from ..arch.generic_instructions import ArtificialInstruction


class OutputStream(metaclass=abc.ABCMeta):
    """ Interface to generate code with.

    Contains the emit function to output instruction to the stream.
    """
    def emit(self, item):  # pragma: no cover
        """ Encode instruction and add symbol and relocation information """
        if isinstance(item, ArtificialInstruction):
            for expanded_instruction in item.render():
                self.emit(expanded_instruction)
        else:
            self.do_emit(item)

    @abc.abstractmethod
    def do_emit(self, item):
        """ Actual emit implementation """
        raise NotImplementedError('Abstract base class')

    def emit_all(self, items):
        """ Emit all items from an iterable """
        for item in items:
            self.emit(item)

    def select_section(self, name):
        """ Switch output to certain section """
        self.emit(SectionInstruction(name))


class TextOutputStream(OutputStream):
    """ Output stream that writes instruction as text. """
    def __init__(self, printer=None, f=None, add_binary=False):
        self.output_file = f
        self.add_binary = add_binary
        if printer:
            self.printer = printer
        else:
            self.printer = AsmPrinter()

    def do_emit(self, item):
        """ Emit the given item """
        assert isinstance(item, Instruction), str(item) + str(type(item))
        txt = self.printer.print_instruction(item)
        if isinstance(item, Label):
            if self.add_binary:
                prefix = 12 * ' '
            else:
                prefix = ''
        else:
            if self.add_binary:
                b = binascii.hexlify(item.encode()).decode('ascii')
                prefix = '{:16}  '.format(b)
            else:
                prefix = '      '
        print(prefix, txt, file=self.output_file)


class BinaryOutputStream(OutputStream):
    """ Output stream that writes to object file """
    def __init__(self, obj_file):
        super().__init__()
        self.obj_file = obj_file
        self.literal_pool = []
        self.current_section = None

    def do_emit(self, item):
        """ Encode instruction and add symbol and relocation information.
        """
        assert isinstance(item, Instruction), str(item) + str(type(item))

        if isinstance(item, SectionInstruction):
            self.current_section = self.obj_file.get_section(
                item.name, create=True)

        assert self.current_section
        section = self.current_section
        address = self.current_section.size
        bin_data = item.encode()
        section.add_data(bin_data)
        for sym in item.symbols():
            self.obj_file.add_symbol(sym, address, section.name)
        for reloc in item.relocations():
            reloc.offset += address
            reloc.section = section.name
            self.obj_file.add_relocation(reloc)

        # Special case for align, TODO do this different?
        if isinstance(item, Alignment):
            while section.size % item.align != 0:
                section.add_data(bytes([0]))
            if item.align > self.current_section.alignment:
                self.current_section.alignment = item.align
        elif isinstance(item, DebugData):
            # We have debug data here!
            self.obj_file.debug_info.add(item.data)


class DummyOutputStream(OutputStream):
    """ Stream that does nothing """
    def do_emit(self, item):
        pass


class FunctionOutputStream(OutputStream):
    """ Stream that emits a string to the given function """
    def __init__(self, function):
        self.function = function

    def do_emit(self, item):
        self.function(item)


class LoggerOutputStream(FunctionOutputStream):
    """ Stream that emits instructions as text in the log """
    def __init__(self):
        self.logger = logging.getLogger('LoggerOutputStream')
        super().__init__(self.logger.debug)


class MasterOutputStream(OutputStream):
    """ Stream that emits to multiple sub streams """
    def __init__(self, substreams=()):
        self.substreams = list(substreams)   # Use copy constructor!!!

    def do_emit(self, item):
        for output_stream in self.substreams:
            output_stream.emit(item)


def binary_and_logging_stream(output):
    """ Create a stream object that both logs and writes to an object file """
    stream1 = BinaryOutputStream(output)
    stream2 = LoggerOutputStream()
    ostream = MasterOutputStream([stream1, stream2])
    return ostream
