""" Module full of bit manipulating helper classes. """

import struct


def rotate_right(v, n):
    """ bit-wise Rotate right n times """
    mask = (2**n) - 1
    mask_bits = v & mask
    return (v >> n) | (mask_bits << (32 - n))


def rotate_left(v, n):
    assert n >= 0
    assert n < 32
    return rotate_right(v, 32 - n)


def encode_imm32(v):
    """ Bundle 32 bit value into 4 bits rotation and 8 bits value """
    for i in range(0, 16):
        v2 = rotate_left(v, i*2)
        if (v2 & 0xFFFFFF00) == 0:
            rotation = i
            val = v2 & 0xFF
            x = (rotation << 8) | val
            return x
    raise ValueError("Invalid value {}".format(v))


def align(value, m):
    """ Increase value to a multiple of m """
    while ((value % m) != 0):
        value = value + 1
    return value


def wrap_negative(value, bits):
    """ Make a bitmask of a value, even if it is a negative value ! """
    mx = 2**bits - 1
    mn = -(2**(bits-1))
    assert value in range(mn, mx)
    b = struct.unpack('<I', struct.pack('<i', value))[0]
    mask = (1 << bits) - 1
    return b & mask


class BitView:
    """ A convenience window on a set of bits, to fiddle them easily
        construct the bitview on a bytearray at a given start index
        and a given length.
    """
    def __init__(self, data, begin, length):
        self.data = data
        self.begin = begin
        self.length = length
        # TODO: implement endianess!

    def __setitem__(self, key, value):
        if type(key) is slice:
            assert key.step is None
            bits = key.stop - key.start
            assert bits > 0
            assert key.stop <= self.length * 8
            limit = 1 << bits
            assert value < limit

            # We can begin, process per byte
            for j in range(self.length):
                bitpos1 = j * 8
                bitpos2 = bitpos1 + 8

                # If we start after the last bit of this byte, carry on
                if key.start >= bitpos2:
                    continue

                # If we stop before the first byte, stop
                if key.stop <= bitpos1:
                    break

                # We are ready to fiddle!
                if key.start > bitpos1:
                    p1 = key.start
                else:
                    p1 = bitpos1

                if key.stop < bitpos2:
                    p2 = key.stop
                else:
                    p2 = bitpos2
                # print('p1, p2=', p1, p2)
                bitsize = p2 - p1
                bitmask = ((1 << bitsize) - 1)

                # Determine the mask:
                mask = bitmask << (p1 - bitpos1)

                # Determine the new value of the bits:
                bits = (bitmask & (value >> (p1 - key.start))) \
                    << (p1 - bitpos1)

                # print('mask', hex(mask), 'bitsize=', bitsize, hex(bits))

                # Determine the byte index:
                idx = self.begin + j

                # Clear bits:
                self.data[idx] &= (0xff ^ mask)

                # Set bits:
                self.data[idx] |= bits
        else:  # pragma: no cover
            raise KeyError()
