""" This module assists with reading and writing wasm to binary.
"""

import struct
from ..utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ..utils.leb128 import unsigned_leb128_decode, signed_leb128_decode


LANG_TYPES = {
    'i32': b'\x7f',
    'i64': b'\x7e',
    'f32': b'\x7d',
    'f64': b'\x7c',
    'anyfunc': b'\x70',
    'func': b'\x60',
    'emptyblock': b'\x40',  # pseudo type for representing an empty block_type
    }
LANG_TYPES_REVERSE = {v[0]: k for k, v in LANG_TYPES.items()}


class FileWriter:
    """ Helper class that can write bytes to a file """

    def __init__(self, f):
        self.f = f

    def write(self, bb):
        return self.f.write(bb)

    def write_f64(self, x):
        self.f.write(struct.pack('<d', x))

    def write_f32(self, x):
        self.f.write(struct.pack('<f', x))

    def write_u32(self, x):
        self.f.write(struct.pack('<I', x))

    def write_str(self, x):
        bb = x.encode('utf-8')
        self.write_vu32(len(bb))
        self.f.write(bb)

    def write_vs64(self, x):
        bb = signed_leb128_encode(x)
        if not len(bb) <= 10:
            raise ValueError('Cannot pack {} into 10 bytes'.format(x))
        self.f.write(bb)

    def write_vs32(self, x):
        bb = signed_leb128_encode(x)
        if not len(bb) <= 5:  # 5 = ceil(32/7)
            raise ValueError('Cannot pack {} into 5 bytes'.format(x))
        self.f.write(bb)

    def write_vu32(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) <= 5
        self.f.write(bb)

    def write_vu7(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) == 1
        self.f.write(bb)

    def write_vu1(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) == 1
        self.f.write(bb)

    def write_type(self, typ: str):
        """ Write type """
        self.write(LANG_TYPES[typ])

    def write_limits(self, min, max):
        if max is None:
            self.write(b'\x00')
            self.write_vu32(min)
        else:
            self.write(b'\x01')
            self.write_vu32(min)
            self.write_vu32(max)

    def write_expression(self, expression):
        """ Write an expression (a list of instructions) """
        for instruction in expression:
            instruction._to_writer(self)
        # Encode explicit end:
        from .components import Instruction
        Instruction('end')._to_writer(self)


class FileReader:
    """ Helper class that can read bytes from a file """

    def __init__(self, f):
        self.f = f
        self._buffer = bytes()
        self._pos = 0

    def read(self, amount=None):
        if amount is not None and amount < 0:
            raise ValueError('Cannot read {} bytes'.format(amount))
        data = self.f.read(amount)
        if amount is not None and len(data) != amount:
            raise EOFError('Reading beyond end of file')
        return data

    def bytefile(self, f):
        b = f.read(1)
        while b:
            yield b[0]
            b = f.read(1)

    def __next__(self):
        b = self.read(1)
        return b[0]

    def read_byte(self):
        """ Read the value of a single byte """
        data = self.read(1)
        return data[0]

    def read_int(self):
        """ Read variable size signed int """
        return signed_leb128_decode(self)

    def read_uint(self):
        """ Read variable size unsigned integer """
        return unsigned_leb128_decode(self)

    def read_f32(self) -> float:
        data = self.read(4)
        value, = struct.unpack('f', data)
        return value

    def read_f64(self) -> float:
        data = self.read(8)
        value, = struct.unpack('d', data)
        return value

    def read_u32(self) -> int:
        return struct.unpack('<I', self.read(4))[0]

    def read_bytes(self) -> bytes:
        """ Read raw bytes data """
        amount = self.read_uint()
        return self.read(amount)

    def read_str(self):
        """ Read a string """
        data = self.read_bytes()
        return data.decode('utf-8')

    def read_type(self):
        """ Read a wasm type """
        tp = self.read_byte()
        return LANG_TYPES_REVERSE[tp]

    def read_limits(self):
        """ Read min and max limits """
        mx_present = self.read(1)[0]
        assert mx_present in [0, 1]
        minimum = self.read_uint()
        if mx_present:
            maximum = self.read_uint()
        else:
            maximum = None
        return minimum, maximum

    def read_expression(self):
        """ Read instructions until an end marker is found """
        expr = []
        blocks = 1
        i = self.read_instruction()
        # keep track of if/block/loop etc:
        if i.opcode == 'end':
            blocks -= 1
        elif i.opcode in ('if', 'block', 'loop'):
            blocks += 1
        expr.append(i)
        while blocks:
            i = self.read_instruction()
            # print(i)
            if i.opcode == 'end':
                blocks -= 1
            elif i.opcode in ('if', 'block', 'loop'):
                blocks += 1
            expr.append(i)

        # Strip of last end opcode:
        assert expr[-1].opcode == 'end'
        return expr[:-1]

    def read_instruction(self):
        """ Read a single instruction """
        # TODO: resolve this import hack:
        from .components import Instruction
        return Instruction(self)
