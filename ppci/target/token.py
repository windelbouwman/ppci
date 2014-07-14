
import struct


def u16(h):
    return struct.pack('<H', h)


def u32(x):
    return struct.pack('<I', x)


def u8(x):
    return struct.pack('<B', x)


def val2bit(v, bits):
    b = []
    for i in range(bits):
        b.append(bool((1 << i) & v))
    return b


def bit_range(b, e):
    """ Property generator function """
    getter = lambda s: s[b:e]

    def setter(s, v):
        s[b:e] = v
    return property(getter, setter)


class Token:
    def __init__(self, bitsize):
        self.bitsize = bitsize
        self.bit_value = 0

    def set_bit(self, i, value):
        value = bool(value)
        assert i in range(0, self.bitsize)
        mask = 1 << i
        if value:
            self.bit_value |= mask
        else:
            self.bit_value &= (~mask)

    def __getitem__(self, key):
        return False

    def __setitem__(self, key, value):
        if type(key) is int:
            self.set_bit(key, value)
        elif type(key) is slice:
            assert key.step is None
            bits = key.stop - key.start
            assert value < (2**bits)
            value_bits = val2bit(value, bits)
            for i in range(key.start, key.stop):
                self.set_bit(i, value_bits[i - key.start])
        else:
            raise KeyError()
