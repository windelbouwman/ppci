
""" Contains disassembler stuff. """

from ..arch.data_instructions import Db


class Disassembler:
    """ Base disassembler for some architecture """
    def __init__(self, arch):
        self.arch = arch
        for instruction in arch.isa.instructions:
            # print(instruction, instruction.patterns)
            # for nl in instruction.non_leaves:
            #    print('  ', nl.patterns)
            pass

    def disasm(self, data, outs, address=0):
        """ Disassemble data into an instruction stream """
        # TODO: implement this!

        # The trial and error method, will be slow as a snail:
        #for instruction in self.arch.isa.instructions:
        #    for size in instruction.sizes():
        #        part = data[:size]
        #        try:
        #            print(instruction, part, size)
        #            i = instruction.decode(part)
        #            print(i)
        #        except ValueError:
        #            pass

        # For now, all is bytes!
        for byte in data:
            ins = Db(byte)
            ins.address = address
            outs.emit(ins)
            address += len(ins.encode())

    def take_one(self):
        pass
