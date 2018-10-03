""" OCaml i/o helpers.
"""


import struct


class FileReader:
    """ OCaml file reader helper with low level primitive read functions. """
    def __init__(self, f):
        self.f = f

    def read_data(self, size):
        # TODO: deprecate?
        return self.f.read(size)

    def read_bytes(self, size):
        return self.f.read(size)

    def read_byte(self):
        return self.read_bytes(1)[0]

    def read_fmt(self, fmt):
        size = struct.calcsize(fmt)
        data = self.read_data(size)
        return struct.unpack(fmt, data)[0]

    def read_u8(self):
        return self.read_fmt('B')

    def read_s8(self):
        return self.read_fmt('b')

    def read_u16(self):
        return self.read_fmt('>H')

    def read_s16(self):
        return self.read_fmt('>h')

    def read_u32(self):
        return self.read_fmt('>I')

    def read_s32(self):
        return self.read_fmt('>i')
