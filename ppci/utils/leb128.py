""" Little Endian Base 128 (LEB128) variable length encoding

https://en.wikipedia.org/wiki/LEB128#Unsigned_LEB128
"""


def signed_leb128_encode(value: int) -> bytes:
    """ Encode the given number as signed leb128 """
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


def unsigned_leb128_encode(value: int) -> bytes:
    """ Encode number as into unsigned leb128 encoding """
    if value < 0:
        raise ValueError('Cannot encode negative number as unsigned leb128')

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


def signed_leb128_decode(data) -> int:
    """ Read variable length encoded 128 bits signed integer """
    result = 0
    shift = 0
    while True:
        byte = next(data)
        result |= (byte & 0x7f) << shift
        shift += 7
        # Detect last byte:
        if byte & 0x80 == 0:
            break

    if byte & 0x40:
        # We have sign bit set!
        mask = (1 << shift) - 1
        result = result ^ mask
        result = -result - 1

    return result


def unsigned_leb128_decode(data) -> int:
    """ Read variable length encoded 128 bits unsigned integer """
    result = 0
    shift = 0
    while True:
        byte = next(data)
        result |= ((byte & 0x7f) << shift)
        # Detect last byte:
        if byte & 0x80 == 0:
            break
        shift += 7
    return result
