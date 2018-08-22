""" Little Endian Base 128 (LEB128) variable length encoding

https://en.wikipedia.org/wiki/LEB128#Unsigned_LEB128
"""


def signed_leb128_encode(value: int) -> bytes:
    """ Encode the given number as signed leb128

    .. doctest::

        >>> from ppci.utils.leb128 import signed_leb128_encode
        >>> signed_leb128_encode(-1337)
        b'\xc7u'

    """
    data = []

    while True:
        byte = value & 0x7F
        value >>= 7  # This is an arithmatic shift right

        # Extract the current sign bit
        sign_bit = bool(byte & 0x40)

        # Check if we are done
        if (value == 0 and not sign_bit) or (value == -1 and sign_bit):
            # We are done!
            data.append(byte)
            break
        else:
            data.append(byte | 0x80)
    return bytes(data)


def unsigned_leb128_encode(value: int) -> bytes:
    """ Encode number as into unsigned leb128 encoding

    .. doctest::

        >>> from ppci.utils.leb128 import unsigned_leb128_encode
        >>> unsigned_leb128_encode(42)
        b'*'
    """
    if not isinstance(value, int):
        raise TypeError('Expected int but got {}'.format(type(value)))

    if value < 0:
        raise ValueError('Cannot encode negative number as unsigned leb128')

    data = []  # ints, really
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            # We are done!
            data.append(byte)
            break
        else:
            data.append(byte | 0x80)  # Append data and continuation marker
    return bytes(data)


def signed_leb128_decode(data) -> int:
    """ Read variable length encoded 128 bits signed integer.

    .. doctest::

        >>> from ppci.utils.leb128 import signed_leb128_decode
        >>> signed_leb128_decode(iter(bytes([0x9b, 0xf1, 0x59])))
        -624485
    """
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
    """ Read variable length encoded 128 bits unsigned integer

    .. doctest::

        >>> from ppci.utils.leb128 import unsigned_leb128_decode
        >>> signed_leb128_decode(iter(bytes([0xe5, 0x8e, 0x26])))
        624485
    """
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
