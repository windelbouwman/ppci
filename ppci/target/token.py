
import struct


def u16(h):
    return struct.pack('<H', h)


def u32(x):
    if x < 0:
        return struct.pack('<i', x)
    else:
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
    __slots__ = ['mask', 'bitsize', 'bit_value']

    def __init__(self, bitsize):
        self.bitsize = bitsize
        self.bit_value = 0
        self.mask = (1 << self.bitsize) - 1

    def set_bit(self, i, value):
        """ Sets a specific bit in this token """
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
            assert bits > 0
            limit = 1 << bits
            assert value < limit
            mask = self.mask ^ ((limit - 1) << key.start)
            self.bit_value &= mask
            self.bit_value |= value << key.start
        else:
            raise KeyError()
