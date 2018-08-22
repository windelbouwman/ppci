""" Utilities to dump binary data in hex """


def hexdump(data, address=0):
    """ Hexdump of the given bytes.
    """
    w = 16
    for piece in chunks(data, chunk_size=w):
        ints = ' '.join(hex(j)[2:].rjust(2, '0') for j in piece)
        chars = ''.join(chr(j) if j in range(33, 127) else '.' for j in piece)
        line = '{}  {}  {}'.format(
            hex(address)[2:].rjust(8, '0'),
            ints.ljust(w * 3 - 1), chars)
        print(line)
        address += w


def chunks(data, chunk_size=16):
    """ Split data into pieces of maximum chunk_size bytes """
    idx = 0
    while idx < len(data):
        s = min(len(data) - idx, chunk_size)
        yield data[idx:idx+s]
        idx += s
