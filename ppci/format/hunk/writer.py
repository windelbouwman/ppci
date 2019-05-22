""" Create Amiga hunk files.
"""

import logging
from . import enums
from ..io import BaseIoWriter


logger = logging.getLogger("hunk-writer")


def write_hunk(filename, code_data):
    """ Write a hunk file.
    """
    with open(filename, "wb") as f:
        writer = Writer(f)
        if len(code_data) % 4:
            padding = 4 - len(code_data) % 4
            code_data += bytes(padding * [0])
        writer.write(code_data)


class Writer(BaseIoWriter):
    """ Writer for amiga hunk files. """

    def write(self, code_data):
        hunk_sizes = [len(code_data) // 4]
        self.write_header(hunk_sizes)
        self.write_code(code_data)
        self.write_u32(enums.HUNK_END)

    def write_header(self, hunk_sizes):
        """ Write a header hunk """
        self.write_u32(enums.HUNK_HEADER)
        self.write_string("")
        first_hunk = last_hunk = 0
        self.write_u32(1)  # table size
        self.write_u32(first_hunk)
        self.write_u32(last_hunk)
        for hunk_size in hunk_sizes:
            self.write_u32(hunk_size)

    def write_code(self, code):
        """ Write a code hunk """
        self.write_u32(enums.HUNK_CODE)
        if len(code) % 4 != 0:
            raise ValueError("Code size not a multiple of 4")
        num_words = len(code) // 4
        self.write_u32(num_words)
        self.f.write(code)

    def write_string(self, value):
        if value == "":
            self.write_u32(0)
        else:
            raise NotImplementedError("TODO")

    def write_u32(self, value):
        self.write_fmt(">I", value)
