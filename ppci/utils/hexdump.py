""" Utilities to dump binary data in hex """


def hexdump(data, address=0):
    """ Hexdump of the given bytes.
    """
    w = 16
    hex_chars_width = w * 3 - 1 + ((w - 1) // 8)
    for piece in chunks(data, chunk_size=w):
        hex_chars = []
        for part8 in chunks(piece, chunk_size=8):
            hex_chars.append(
                ' '.join(hex(j)[2:].rjust(2, '0') for j in part8))
        ints = '  '.join(hex_chars)
        chars = ''.join(chr(j) if j in range(33, 127) else '.' for j in piece)
        line = '{}  {}  |{}|'.format(
            hex(address)[2:].rjust(8, '0'),
            ints.ljust(hex_chars_width),
            chars
        )
        print(line)
        address += w


def chunks(data, chunk_size=16):
    """ Split data into pieces of maximum chunk_size bytes """
    idx = 0
    while idx < len(data):
        s = min(len(data) - idx, chunk_size)
        yield data[idx:idx+s]
        idx += s
