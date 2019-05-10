""" Read a CODE block.
"""

import io
import logging
from .opcodes import Instrs, Instruction, Opcode
from .io import FileReader


logger = logging.getLogger("ocaml")


def load_code(data: bytes):
    if len(data) % 4 != 0:
        raise ValueError("codesize must be a multiple of 4")
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
        logger.debug("Read %s instructions", len(instructions))
        return instructions

    def read_instr(self):
        """ Read a single instruction """
        label = self.nr
        opcode = self.read_word()
        if opcode not in Instrs:
            raise ValueError("Unknown opcode %s" % opcode)

        name, arg_names = Instrs[opcode]
        if opcode == Opcode.SWITCH:
            n = self.read_word()
            size_tag = n >> 16
            size_long = n & 0xFFFF
            size = size_tag + size_long
            tab = []
            for _ in range(size):
                tab.append(self.read_word())
            args = [n, tab]
        elif opcode == Opcode.CLOSUREREC:
            f = self.read_word()
            v = self.read_word()
            o = self.read_word()
            t = []
            for _ in range(f - 2):
                t.append(self.read_word())
            args = [f, v, o, t]
        else:
            # Normal opcode:
            args = []
            for arg_name in arg_names:
                # if arg_name in ['n', 's', 'ofs', 's', 't', 'p']:
                if True:
                    arg = self.read_word()
                else:
                    raise NotImplementedError(arg_name)
                args.append(arg)
        # print(label, name, args)
        ins = Instruction(opcode, name, args)
        ins.label = label
        return ins

    def read_word(self):
        self.nr += 1
        return self.reader.read_fmt("<I")
