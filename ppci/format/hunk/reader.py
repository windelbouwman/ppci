""" Hunk file loading.

Functionality to process Amiga hunk files.

Sort of taken from here:

http://amiga-dev.wikidot.com/file-format:hunk#toc42

"""

import struct
import logging
from . import enums

logger = logging.getLogger("hunk")


def read_hunk(filename):
    """ Read a hunk file. """
    logger.debug("Loading hunk file from %s", filename)
    with open(filename, "rb") as f:
        reader = Reader()
        reader.read(f)


class Reader:
    """ Process an amiga hunk file.
    """

    def read(self, f):
        self.f = f
        while True:
            hunk_id = self.read_u32()
            logger.debug(
                "Reading hunk 0x%X (%s)", hunk_id, enums.get_name(hunk_id)
            )
            if hunk_id == enums.HUNK_HEADER:
                self.read_header()
            elif hunk_id == enums.HUNK_CODE:
                self.read_code()
            elif hunk_id == enums.HUNK_DATA:
                self.read_data()
            elif hunk_id == enums.HUNK_BSS:
                self.read_u32()
            elif hunk_id == enums.HUNK_DREL32:
                self.read_drel32()
            elif hunk_id == enums.HUNK_SYMBOL:
                self.read_symbol()
            elif hunk_id == enums.HUNK_END:
                break
            else:
                raise NotImplementedError(
                    "hunk type not implemented: 0x{:X}".format(hunk_id)
                )

    def read_header(self):
        """ Read a header hunk """
        names = []
        while True:
            name = self.read_string()
            if name == "":
                break
            names.append(name)
        table_size = self.read_u32()
        logger.debug("table size: %s", table_size)
        first_hunk = self.read_u32()
        last_hunk = self.read_u32()
        num_hunks = last_hunk - first_hunk + 1
        logger.debug("Hunk file with %s hunks", num_hunks)
        hunk_sizes = []
        for i in range(num_hunks):
            hunk_size = self.read_u32()
            logger.debug(
                "Hunk size %s = %s words (%s bytes)",
                i,
                hunk_size,
                hunk_size * 4,
            )
            hunk_sizes.append(hunk_size)

    def read_code(self):
        """ Read code hunk. """
        num_longs = self.read_u32()
        size = num_longs * 4
        logger.debug("Code section of %s words (%s bytes)", num_longs, size)
        data = self.f.read(size)
        return data

    def read_data(self):
        """ Read data hunk. """
        num_longs = self.read_u32()
        data = self.f.read(num_longs * 4)
        return data

    def read_drel32(self):
        """ Read some form of relocation data """
        num_offsets = self.read_u16()
        hunk_number = self.read_u16()
        logger.debug(
            "Reading %s offsets for hunk %s", num_offsets, hunk_number
        )
        offsets = []
        for _ in range(num_offsets):
            offset = self.read_u16()
            offsets.append(offset)
        if num_offsets & 1:
            logger.debug("Reading an additional word to align at long word")
            self.read_u16()
        return hunk_number, offsets

    def read_symbol(self):
        """ Read symbol information """
        symbols = []
        while True:
            name = self.read_string()
            if not name:
                break
            offset = self.read_u32()
            logger.debug("Read symbol %s at offset %s", name, offset)
            symbols.append((name, offset))
        return symbols

    def read_string(self):
        """ Read a string. """
        num_longs = self.read_u32()
        if num_longs < 1:
            s = ""
        else:
            data = self.f.read(num_longs * 4)
            idx = data.find(0)
            s = data[:idx].decode("ascii")
        logger.debug('Read string: "%s"', s)
        return s

    def read_u32(self):
        return self.read_fmt(">I")[0]

    def read_u16(self):
        return self.read_fmt(">H")[0]

    def read_fmt(self, fmt):
        size = struct.calcsize(fmt)
        data = self.f.read(size)
        return struct.unpack(fmt, data)
