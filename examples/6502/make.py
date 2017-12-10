
import sys
import struct
import os
from ppci import api
from ppci.utils.reporting import HtmlReportGenerator

arch = api.get_arch('mcs6500')
print('Using arch', arch)


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


if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
        text_message = f.read()
else:
    text_message = 'you can provide a text file to customize this message'


with open('report.html', 'w') as f2, HtmlReportGenerator(f2) as reporter:
    with open('add.c') as f:
        oj = api.cc(f, arch, reporter=reporter)
    print(oj)

    with open('hello.s') as f:
        oj = api.asm(f, arch)
    oj = api.link([oj], layout='layout.mmp')
    print(oj)

    with open(os.path.join('c64disk', 'hello.prg'), 'wb') as f:
        # Generate tokenized basic:
        basic_program = bytes([
            0x01, 0x08,  # Load address
            0x09, 0x08,  # start of the next line
            0x0a, 0x00,  # line number 10 word in little endianness
            # 0x9e, 0x20, 0x34, 0x30, 0x39, 0x36, 0x00,  # SYS 4096
            0x99,  # Print token!
            0x20, 0x31,  # Space and number 1
            0x0,  # End of line
            0x1a, 0x00,  # 0x1a line number in little endianness
            0x99,  # Print token!
            0x20, 0x22  # Space and "
        ])
        txt = text_message.upper().encode('ascii')
        basic_program += txt
        basic_program += bytes([
            0x22,  # "
            0x0,  # End of line
            0x00, 0x00  # End of program
            # 0x80,  # END
        ])
        # f.write(basic_program)
        program = [
            BasicLine(12, bytes([0x99, 0x20, 0x31])),
        ]
        for nr, line in enumerate(text_message.split('\n')):
            line = line.strip().upper().encode('ascii')
            program.append(
                BasicLine(
                    30 + nr,
                    bytes([0x99, 0x20, 0x22]) + line + bytes([0x22])))
        write_basic_program(program, f)

        f.write(oj.get_image('upperram').data)
