""" Read a CODE block.
"""

import io
import logging
from .opcodes import Instrs
from .io import FileReader


logger = logging.getLogger('ocaml')


def load_code(data: bytes):
    if len(data) % 4 != 0:
        raise ValueError('codesize must be a multiple of 4')
    reader = FileReader(io.BytesIO(data))
    return CodeReader(reader, len(data)).read()


class CodeReader:
    def __init__(self, reader, size):
        self.reader = reader
        self.size = size
        self.nr = 0

    def read(self):
        instructions = []
        self.nr = 0
        while self.reader.f.tell() < self.size:
            instruction = self.read_instr()
            instructions.append(instruction)
        return instructions

    def read_instr(self):
        """ Read a single instruction """
        label = self.nr
        opcode = self.read_word()
        if opcode in Instrs:
            name, arg_names = Instrs[opcode]
            args = []
            for arg_name in arg_names:
                arg = self.read_word()
                args.append(arg)
        else:
            logger.warning('Unknown opcode %s', opcode)
            name = '???'
            args = []
        # print(label, name, args)
        return (label, name, args)

    def read_word(self):
        self.nr += 1
        return self.reader.read_fmt('<I')
