import struct


def u16(h):
    return struct.pack('<H', h)


def u32(x):
    if x < 0:
        return struct.pack('<i', x)
    else:
        return struct.pack('<I', x)


def u64(x):
    if x < 0:
        return struct.pack('<q', x)
    else:
        return struct.pack('<Q', x)


def u8(x):
    return struct.pack('<B', x)


def val2bit(v, bits):
    b = []
    for i in range(bits):
        b.append(bool((1 << i) & v))
    return b


class _p2(property):
    def __init__(self, getter, setter, bitsize):
        assert bitsize > 0
        self._bitsize = bitsize
        self._mask = (1 << bitsize) - 1
        super().__init__(getter, setter)


def bit_range(b, e):
    """ Property generator function """
    def getter(s):
        return s[b:e]

    def setter(s, v):
        s[b:e] = v
    return _p2(getter, setter, e - b)


def bit(b):
    """ Return a property that sets a single bit """
    return bit_range(b, b + 1)


def bit_concat(*partials):
    """ Group several fields together into a single usable field """
    def getter(s):
        v = 0
        for at in partials:
            v = v << at._bitsize
            v = v | (at.__get__(s) & at._mask)
        return v

    def setter(s, v):
        for at in reversed(partials):
            at.__set__(s, v & at._mask)
            v = v >> at._bitsize
    bitsize = sum(at._bitsize for at in partials)
    return _p2(getter, setter, bitsize)


class Token:
    """ A token in a stream """
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
        if type(key) is slice:
            assert key.step is None
            bits = key.stop - key.start
            assert bits > 0
            limit = 1 << bits
            mask = (limit - 1) << key.start
            value = (self.bit_value & mask) >> key.start
            return value
        else:
            raise KeyError(key)

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
            raise KeyError(key)
