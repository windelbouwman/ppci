
"""
    Contains disassembler stuff.
"""

from ..arch.data_instructions import Db


class Disassembler:
    """ Base disassembler for some architecture """
    def __init__(self, arch):
        self.arch = arch

    def disasm(self, data, outs, address=0):
        """ Disassemble some data at an address into an instruction stream """
        # For now, all is bytes!
        # TODO: implement this!
        for byte in data:
            ins = Db(byte)
            ins.address = address
            outs.emit(ins)
            address += len(ins.encode())
