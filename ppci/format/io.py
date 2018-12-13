""" Base reader and writer classes.

Reading file formats is often more of the same. This module contains commonly
required logic to process binary files.
"""

import struct


class BaseIoReader:
    def __init__(self, f):
        self.f = f

    def read_fmt(self, fmt):
        size = struct.calcsize(fmt)
        data = self.read_data(size)
        return struct.unpack(fmt, data)[0]

    def read_data(self, size):
        # TODO: deprecate?
        return self.f.read(size)

    def read_bytes(self, size):
        return self.f.read(size)


class BaseIoWriter:
    def __init__(self, f):
        self.f = f

    def write_fmt(self, fmt, value):
        data = struct.pack(fmt, value)
        self.f.write(data)
