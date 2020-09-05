
import sys
import os
from ppci import api
from ppci.utils.reporting import html_reporter
from ppci.lang.basic.c64 import BasicLine, write_basic_program

arch = api.get_arch('mcs6500')
print('Using arch', arch)


if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
        text_message = f.read()
else:
    text_message = 'you can provide a text file to customize this message'


with html_reporter('report.html') reporter:
    with open('add.c') as f:
        oj = api.cc(f, arch, reporter=reporter)
    print(oj)

    with open('hello.s') as f:
        oj = api.asm(f, arch)
    oj = api.link([oj], layout='layout.mmp')
    print(oj)

    with open(os.path.join('c64disk', 'hello.prg'), 'wb') as f:
        # Generate tokenized basic:
        load_address = 0x801
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
        sys_address = 0x890
        address_text = str(sys_address).encode('ascii')
        program.append(BasicLine(1000, bytes([0x9e]) + address_text))
        write_basic_program(program, f)
        pos = f.tell() - 2
        max_basic_size = sys_address - load_address
        if pos < max_basic_size:
            f.seek(sys_address - load_address + 2)
            print(pos)

            f.write(oj.get_image('upperram').data)
        else:
            print('Basic program too large')
