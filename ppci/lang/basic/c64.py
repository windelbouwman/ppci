""" Commodore 64 basic """

import struct


class BasicLine:
    """ A single line in a basic program """
    def __init__(self, label, command):
        self.label = label
        self.command = command

    def encode(self, address) -> bytes:
        """ Encode the basic line into tokenized basic format """
        next_address = address + 5 + len(self.command)
        header = struct.pack('<HH', next_address, self.label)
        end_marker = bytes([0])
        return header + self.command + end_marker


def write_basic_program(program, f) -> bytes:
    """ Write a basic program to file """
    address = 0x0801
    f.write(struct.pack('<H', address))  # Load address
    for line in program:
        encoded = line.encode(address)
        address += len(encoded)
        f.write(encoded)
    f.write(bytes([0x00, 0x00]))  # End of program marker
