""" Module full of bit manipulating helper classes. """


def rotate_right(v, n):
    """ bit-wise Rotate right n times """
    mask = (2 ** n) - 1
    mask_bits = v & mask
    return (v >> n) | (mask_bits << (32 - n))


def rotate_left(v, n):
    assert n >= 0
    assert n < 32
    return rotate_right(v, 32 - n)


def rotl(v, count, bits):
    """ Rotate v left count bits """
    mask = (1 << bits) - 1
    count = count % bits
    return (((v << count) & mask) | (v >> (bits - count)))


def rotr(v, count, bits):
    """ Rotate v right count bits """
    mask = (1 << bits) - 1
    count = count % bits
    return ((v >> count) | ((v << (bits - count)) & mask))


def to_signed(value, bits):
    return correct(value, bits, True)


def to_unsigned(value, bits):
    return correct(value, bits, False)


def correct(value, bits, signed):
    base = 1 << bits
    value %= base
    if signed and value.bit_length() == bits:
        return value - base
    else:
        return value


def clz(v: int, bits: int) -> int:
    """ count leading zeroes """
    mask = 1 << (bits - 1)
    count = 0
    while (count < bits) and (v & mask) == 0:
        count += 1
        v = v * 2
    return count


def ctz(v: int, bits: int) -> int:
    """ count trailing zeroes """
    count = 0
    while count < bits and (v % 2) == 0:
        count += 1
        v //= 2
    return count


def popcnt(v: int, bits: int) -> int:
    """ count number of one bits """
    count = 0
    for i in range(bits):
        if v & (1 << i):
            count += 1
    return count


def value_to_bits(v, bits):
    """ Convert a value to a list of booleans """
    b = []
    for i in range(bits):
        b.append(bool((1 << i) & v))
    return b


def bits_to_bytes(bits):
    """ Convert a sequence of booleans into bytes """
    while len(bits) % 8 != 0:
        bits.append(False)

    m = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for j in range(8):
            if bits[i+j]:
                v = v | (1 << j)
        m.append(v)
    return bytes(m)


def encode_imm32(v):
    """ Bundle 32 bit value into 4 bits rotation and 8 bits value """
    for i in range(0, 16):
        v2 = rotate_left(v, i * 2)
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
    upper_limit = (1 << (bits)) - 1
    lower_limit = -(1 << (bits - 1))
    if value not in range(lower_limit, upper_limit + 1):
        raise ValueError('Cannot encode {} in {} bits [{},{}]'.format(
            value, bits, lower_limit, upper_limit))
    mask = (1 << bits) - 1
    bit_value = value & mask  # Performing bitwise and makes it 2 complement.
    assert bit_value >= 0
    return bit_value


def inrange(value, bits):
    """ Test if a signed value can be fit into the given number of bits """
    upper_limit = 1 << (bits - 1)
    lower_limit = -(1 << (bits - 1))
    return value in range(lower_limit, upper_limit)


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
                bits = (
                    bitmask & (value >> (p1 - key.start))) << (p1 - bitpos1)

                # print('mask', hex(mask), 'bitsize=', bitsize, hex(bits))

                # Determine the byte index:
                idx = self.begin + j

                # Clear bits:
                self.data[idx] &= (0xff ^ mask)

                # Set bits:
                self.data[idx] |= bits
        else:  # pragma: no cover
            raise KeyError()
