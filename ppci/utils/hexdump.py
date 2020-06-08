""" Utilities to dump binary data in hex """
from .chunk import chunks


def hexdump(data, address=0, width=16):
    """ Hexdump of the given bytes.

    For example:

        >>> from ppci.utils.hexdump import hexdump
        >>> data = bytes(range(10))
        >>> hexdump(data, width=4)
        00000000  00 01 02 03  |....|
        00000004  04 05 06 07  |....|
        00000008  08 09        |..|

    """
    hex_chars_width = width * 3 - 1 + ((width - 1) // 8)
    for piece in chunks(data, size=width):
        hex_chars = []
        for part8 in chunks(piece, size=8):
            hex_chars.append(" ".join(hex(j)[2:].rjust(2, "0") for j in part8))
        ints = "  ".join(hex_chars)
        chars = "".join(chr(j) if j in range(33, 127) else "." for j in piece)
        line = "{}  {}  |{}|".format(
            hex(address)[2:].rjust(8, "0"), ints.ljust(hex_chars_width), chars
        )
        print(line)
        address += width
