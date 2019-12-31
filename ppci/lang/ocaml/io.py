""" OCaml i/o helpers.
"""


from ...format.io import BaseIoReader


class FileReader(BaseIoReader):
    """ OCaml file reader helper with low level primitive read functions. """

    def read_byte(self):
        return self.read_bytes(1)[0]

    def read_u8(self):
        return self.read_fmt("B")

    def read_s8(self):
        return self.read_fmt("b")

    def read_u16(self):
        return self.read_fmt(">H")

    def read_s16(self):
        return self.read_fmt(">h")

    def read_u32(self):
        return self.read_fmt(">I")

    def read_s32(self):
        return self.read_fmt(">i")
