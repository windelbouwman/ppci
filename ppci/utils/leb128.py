
""" Little Endian Base 128 (LEB128) variable length encoding

https://en.wikipedia.org/wiki/LEB128#Unsigned_LEB128
"""


def signed_leb128_encode(value):
    bb = []
    if value < 0:
        unsignedRefValue = (1 - value) * 2
    else:
        unsignedRefValue = value * 2

    while True:
        byte = value & 0x7F
        value >>= 7
        unsignedRefValue >>= 7
        if unsignedRefValue != 0:
            byte = byte | 0x80
        bb.append(byte)
        if unsignedRefValue == 0:
            break
    return bytes(bb)


def unsigned_leb128_encode(value):
    bb = []  # ints, really
    while True:
        byte = value & 0x7F
        value >>= 7
        if value != 0:
            byte = byte | 0x80
        bb.append(byte)
        if value == 0:
            break
    return bytes(bb)
