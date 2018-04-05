""" Generic file header helper.

This can be seen as a follow up of the struct module [1] or the
construct module [2].

[1]

[2] http://construct.readthedocs.io/en/latest

"""


import struct


# TODO: deprecate this header!
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


# Programmatically define headers:

def mk_header(name, fields):
    """ Create a type which can parse this kind of header """
    members = {
        '_fields': fields,
    }
    size = 0
    for field in fields:
        if field.name is not None:
            members[field.name] = field
        size += field.size
    members['size'] = size
    type_name = '{}Header'.format(name)
    return type(type_name, (BaseHeader,), members)


class BaseHeader:
    """ Base header """
    def __init__(self):
        self._field_values = {}
        for field in self._fields:
            if field.name is not None:
                self._field_values[field.name] = 0

    def __getitem__(self, key):
        return self._field_values[key]

    def write(self, f):
        data = self.serialize()
        f.write(data)

    @classmethod
    def read(cls, f):
        data = f.read(cls.size)
        assert cls.size == len(data)
        return cls.deserialize(data)

    def print(self):
        """ Print all fields in this header """
        for field in self._fields:
            if field.name:
                value = getattr(self, field.name)
                print('{}: {}'.format(field.name, hex(value)))

    def serialize(self):
        data = bytearray()
        for field in self._fields:
            if field.name is not None:
                value = getattr(self, field.name)
            else:
                value = 0
            x = field.encode(value)
            data.extend(x)
        return bytes(data)

    @classmethod
    def deserialize(cls, data):
        hdr = cls()
        offset = 0
        for field in hdr._fields:
            part = data[offset:offset+field.size]
            value = field.decode(part)
            if field.name is not None:
                setattr(hdr, field.name, value)
            offset += field.size
        assert offset == cls.size
        return hdr


class HeaderField(property):
    """ A optionally named field in a header """
    def __init__(self, name=None, size=None):
        self.name = name
        self.size = size

        def fget(self2):
            return self2._field_values[name]

        def fset(self2, value):
            assert isinstance(value, int)
            self2._field_values[name] = value

        super().__init__(fget, fset)


class Const(HeaderField):
    def __init__(self, value):
        super().__init__(name=None, size=len(value))
        self.value = value

    def encode(self, value):
        return self.value

    def decode(self, data):
        assert data == self.value


def Uint8(name=None):
    return FormatField(name, 'B')


Byte = Uint8


def Int16(name=None):
    """ 16 bits signed integer value """
    return FormatField(name, 'h')


def Uint16(name=None):
    """ 16 bits unsigned integer value """
    return FormatField(name, 'H')


class Int24(HeaderField):
    """ 24 bits signed integer value """
    pass


def Int32(name=None):
    """ 32 bits signed integer value """
    return FormatField(name, 'i')


def Uint32(name=None):
    """ 32 bits unsigned integer value """
    return FormatField(name, 'I')


def Int64(name=None):
    """ 64 bits signed integer value """
    return FormatField(name, 'Q')


def Uint64(name=None):
    """ 64 bits unsigned integer value """
    return FormatField(name, 'Q')


class FormatField(HeaderField):
    """ Field which uses ``struct`` to pack and unpack data """
    def __init__(self, name, fmt):
        self.packer = struct.Struct(fmt)
        super().__init__(name=name, size=self.packer.size)

    def encode(self, value):
        return self.packer.pack(value)

    def decode(self, data):
        return self.packer.unpack(data)[0]


def Padding(amount):
    """ Add `amount` bytes of padding """
    pass
