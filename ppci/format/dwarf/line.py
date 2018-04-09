
""" Encode line number programs """
import abc
import operator
import functools

from ...utils import leb128
from .. import header


class LineNumberProgram:
    """ Line number program.

    A line number program contains a series of operations which when
    executed create a table.
    """
    def __init__(self, instructions=()):
        self.instructions = list(instructions)

    def show(self):
        """ Display line number program """
        for instruction in self.instructions:
            print(instruction)

    def run(self):
        """ Run the program, resulting in a line number table """
        context = ExecutionContext(False)
        for instruction in self.instructions:
            instruction.execute(context)
        context.print_table()

    def encode(self):
        """ Encode the program into bytes """
        return functools.reduce(
            operator.add,
            (i.encode() for i in self.instructions))

    @classmethod
    def decode(cls, data):
        raise NotImplementedError()


def table_to_program(table):
    """ Create a line number program from the given line number table """
    instructions = []
    return LineNumberProgram(instructions)


class ExecutionContext:
    """ The line number fsm. """
    def __init__(self, default_is_stmt):
        # Registers:
        self.address = 0
        self.file = 1
        self.line = 1
        self.column = 0
        self.is_stmt = default_is_stmt
        self.basic_block = False
        self.end_sequence = False
        self.prologue_end = False
        self.epilogue_begin = False
        self.isa = 0

        # Line number table:
        self._table = []

    def emit_row(self):
        row = [self.address, self.file, self.line]
        self._table.append(row)

    def print_table(self):
        for row in self._table:
            print(row)


# Opcodes for line number programs:
class Opcode(metaclass=abc.ABCMeta):
    """ A single line number program instruction """
    fields = ()

    @abc.abstractmethod
    def execute(self, context):
        raise NotImplementedError()

    # @abc.abstractmethod
    def encode(self):
        """ Encode this instruction into bytes """
        data = [bytes([self.opcode])]
        for field_name, field_type in self.fields:
            value = getattr(self, field_name)
            if field_type:
                data.append(leb128.signed_leb128_encode(value))
            else:
                data.append(leb128.unsigned_leb128_encode(value))
        print(data)
        return functools.reduce(operator.add, data)


class Copy(Opcode):
    """ Enter current state machine state as row into matrix """
    opcode = 0x01

    def __str__(self):
        return 'DW_LNS_copy'

    def execute(self, context):
        context.emit_row()


class AdvancePc(Opcode):
    """ Modify address """
    opcode = 0x02
    fields = (('amount', False),)

    def __init__(self, amount):
        self.amount = amount

    def __str__(self):
        return 'DW_LNS_advance_pc <{}>'.format(self.amount)

    def execute(self, context):
        context.address += self.amount


class AdvanceLine(Opcode):
    opcode = 0x03
    fields = (('amount', True),)

    def __init__(self, amount):
        self.amount = amount

    def __str__(self):
        return 'DW_LNS_advance_line <{}>'.format(self.amount)

    def execute(self, context):
        context.line += self.amount


class SetFile(Opcode):
    """ DW_LNS_set_file """
    opcode = 0x04
    fields = (('file', False),)

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return 'DW_LNS_set_file <{}>'.format(self.file)

    def execute(self, context):
        context.file = self.file


class SetColumn(Opcode):
    """ Set column """
    opcode = 0x05
    fields = (('column', False),)

    def __init__(self, column):
        self.column = column

    def __str__(self):
        return 'DW_LNS_set_column <{}>'.format(self.column)

    def execute(self, context):
        context.column = self.column


class NegateStmt(Opcode):
    """ Negate is_stmt field """
    opcode = 0x06

    def __str__(self):
        return 'DW_LNS_negate_stmt'

    def execute(self, context):
        context.is_stmt = not context.is_stmt


class SetBasicBlock(Opcode):
    """ Sets `basic_block` to `true` """
    opcode = 0x07

    def __str__(self):
        return 'DW_LNS_set_basic_block'


class SetPrologueEnd:
    opcode = 0x0a

    def __str__(self):
        return 'DW_LNS_set_prologue_end'

    def execute(self, context):
        context.prologue_end = True


class SetEpilogueBegin:
    """ Set `epilogue_begin` to true """
    opcode = 0x0b

    def __str__(self):
        return 'DW_LNS_set_epilogue_begin'

    def execute(self, context):
        context.epilogue_begin = True


class SetIsa(Opcode):
    opcode = 0x0c
    fields = (('isa', False),)

    def __init__(self, isa):
        self.isa = isa

    def __str__(self):
        return 'DW_LNS_set_isa {}'.format(self.isa)

    def execute(self, context):
        context.isa = self.isa
