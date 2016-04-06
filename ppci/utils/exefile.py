
"""
    Implements the exe file format used by windows.
"""

import struct


class Header:
    def __init__(self, fmt):
        self.s = struct.Struct(fmt)

    def write(self, f):
        data = self.serialize()
        f.write(data)

    @property
    def size(self):
        return self.s.size

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self):
        raise NotImplementedError()


class DosHeader(Header):
    """ Representation of the dos header """
    def __init__(self):
        fmt = '< 14H 4H 2H 10H I'
        super().__init__(fmt)
        # one page is 512 bytes
        # one paragraph is 16 bytes
        self.e_magic = 0x5A4D  # magic id 'MZ' (Mark Zbikowski)
        self.e_cblp = 0   # bytes on last page
        self.e_cp = 0  # pages in file, one page is 512 bytes
        self.e_crlc = 0  # relocations
        self.e_cparhdr = 4  # size of header in paragraphs
        self.e_minalloc = 0  # mininum extra paragraphs of memory needed
        self.e_maxalloc = 0xffff  # maximum extra memory required, if not all
        self.e_ss = 0  # initial ss value
        self.e_sp = 0xb8  # initial sp value
        self.e_csum = 0  # Checksum
        self.e_ip = 0  # initial ip value
        self.e_cs = 0  # initial cs value
        self.e_lfarlc = 0  # file address of relocation table
        self.e_ovno = 0  # overlay number, 0 means main program
        # 4 reserved words
        self.e_oemid = 0
        self.e_oeminfo = 0
        # 10 reserved words
        self.e_lfanew = 0  # file address of new exe header

    def serialize(self):
        assert self.size == self.e_cparhdr * 16
        return self.s.pack(
            self.e_magic,
            self.e_cblp,
            self.e_cp,
            self.e_crlc,
            self.e_cparhdr,
            self.e_minalloc,
            self.e_maxalloc,
            self.e_ss,
            self.e_sp,
            self.e_csum,
            self.e_ip,
            self.e_cs,
            self.e_lfarlc,
            self.e_ovno,
            0, 0, 0, 0,
            self.e_oemid,
            self.e_oeminfo,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            self.e_lfanew
            )

    def deserialize(self):
        raise NotImplementedError()


def write_dos_stub(f):
    """ Write dos stub to file. This stub prints to stdout:
        'this program cannot be run in dos mode'
    """
    # TODO: it is nice to have this l33t-code here, but it would also be
    # awesome to invoke the ppci machinery here!
    code = bytearray([
        0x0e,              # push cs
        0x1f,              # pop ds
        0xba, 0xe, 0x0,    # mov dx, message
        0xb4, 0x09,        # mov ah, 09
        0xcd, 0x21,        # int 0x21
        0xb8, 0x01, 0x4c,  # mov ax, 0x4c01
        0xcd, 0x21,        # int 0x21
    ])
    asm_src = """
    push cs
    pop ds
    mov dx, message
    mov ah, 9
    int 0x21
    mov ax, 0x4c01
    int 0x21
    """
    from ..api import asm
    # asm(asm_src)
    code += 'This program can certainly not be run in DOS :-)'.encode('ascii')
    code += bytes([0xd, 0xd, 0xa, ord('$')])
    f.write(code)


class PeHeader(Header):
    pass


class ExeWriter:
    def write(self, obj, f):
        """ Write object to exe file """
        dos_header = DosHeader()
        dos_header.write(f)
        write_dos_stub(f)
        dos_header.e_lfanew = f.tell()   # Link to new PE header:

        # pe_header = PeHeader()
        # pe_header.write(f)

        # Write dos header again:
        f.seek(0)
        dos_header.write(f)
