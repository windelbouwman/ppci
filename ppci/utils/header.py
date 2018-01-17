""" Generic file header helper """

import struct


class Header:
    """ Base header structure.

    Inherit this class to define a file header.
    """
    _byte_order = '<'
    _fields = None

    def __init__(self):
        if self._fields is not None:
            # No padding bytes when using < or > endianness
            fmt = self._byte_order + ''.join(f[1] for f in self._fields)
            self.s = struct.Struct(fmt)

    def write(self, f):
        data = self.serialize()
        f.write(data)

    @property
    def size(self):
        return self.s.size

    def serialize(self):
        values = []
        for f in self._fields:
            name, ty = f
            if name is None:
                value = 0
            else:
                value = getattr(self, name, 0)

            if ty in 'IiHh' and not isinstance(value, int):
                raise TypeError(
                    'Field {} is set to {} which is not of type int'.format(
                        name, value))
            values.append(value)
        return self.s.pack(*values)

    def is_null(self):
        """ Check if all fields are zero """
        return sum(self.serialize()) == 0

    def print(self):
        """ Print all fields in this header """
        for field in self._fields:
            name = field[0]
            if name:
                value = getattr(self, name)
                print('{}: {}'.format(name, hex(value)))

    @classmethod
    def deserialize(cls, f):
        fmt = '<' + ''.join(f[1] for f in cls._fields)
        s = struct.Struct(fmt)
        size = s.size
        data = f.read(size)
        assert len(data) == size
        values = s.unpack(data)
        assert len(values) == len(cls._fields)
        d = cls()
        for field, value in zip(cls._fields, values):
            name = field[0]
            if name:
                setattr(d, name, value)
        return d
