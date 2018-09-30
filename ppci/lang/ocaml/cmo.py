""" Read / write cmo files.
"""

import enum
import struct
import logging
from .opcodes import Instrs

logger = logging.getLogger('ocaml')

MAGIC_V023 = "Caml1999O023"


def read_file(filename):
    if isinstance(filename, str):
        logging.info('Processing %s', filename)
        with open(filename, 'rb') as f:
            return read_file(f)
    else:
        f = filename
        reader = CmoReader(f)
        return reader.read()


INTEXT_MAGIC_NUMBER_SMALL = 0x8495a6be
INTEXT_MAGIC_NUMBER_BIG = 0x8495a6bf

compilation_unit = (
    ('cu_name', 'string'),
    ('cu_pos', 'int'),
    ('cu_codesize', 'int'),
    ('cu_reloc', 'int'),
    ('cu_imports', 'int'),
    ('cu_required_globals', 'int'),
    ('cu_primitives', ('string', 'list')),
    ('cu_force_link', 'bool'),
    ('cu_debug', 'int'),
    ('cu_debugsize', 'int'),
)


class MarshallCode(enum.IntEnum):
    PREFIX_SMALL_BLOCK = 0x80
    PREFIX_SMALL_INT = 0x40
    PREFIX_SMALL_STRING = 0x20
    CODE_INT8 = 0x0
    CODE_INT16 = 0x1
    CODE_INT32 = 0x2
    CODE_INT64 = 0x3
    CODE_SHARED8 = 0x4
    CODE_SHARED16 = 0x5
    CODE_SHARED32 = 0x6
    CODE_SHARED64 = 0x14
    CODE_BLOCK32 = 0x8
    CODE_BLOCK64 = 0x13
    CODE_STRING8 = 0x9
    CODE_STRING32 = 0xA
    CODE_STRING64 = 0x15
    CODE_DOUBLE_BIG = 0xB
    CODE_DOUBLE_LITTLE = 0xC
    CODE_ARRAY8_BIG = 0xD
    CODE_ARRAY8_LITTLE = 0xE
    CODE_ARRAY32_BIG = 0xF
    CODE_ARRAY32_LITTLE = 0x7
    CODE_ARRAY64_BIG = 0x16
    CODE_ARRAY64_LITTLE = 0x17
    CODE_CODEPOINTER = 0x10
    CODE_INFIXPOINTER = 0x11


class Marshall:
    def read32(self):
        data = self.read_data(4)
        return struct.unpack('>I', data)[0]


class Header:
    pass


class CmoReader:
    def __init__(self, f):
        self.f = f

    def read(self):
        self.read_magic()
        # self.read_code()
        offset = self.read_u32()
        print(offset)
        self.f.seek(offset)
        cu_unit = self.read_value(compilation_unit)
        print(cu_unit)
        cu_pos = cu_unit[1]
        cu_codesize = cu_unit[2]
        end_pos = cu_pos + cu_codesize
        assert end_pos <= offset
        if cu_codesize % 4 != 0:
            raise ValueError('codesize must be a multiple of 4')
        # Load code:
        self.f.seek(cu_pos)
        while self.f.tell() < end_pos:
            ins = self.read_instr()
        # print(self.read_u8())

    def read_instr(self):
        """ Read a single instruction """
        w = self.read_word()
        name, arg_names = Instrs[w]
        args = []
        for arg_name in arg_names:
            arg = self.read_word()
            args.append(arg)
        print(name, args)

    def read_word(self):
        return self.read_fmt('<I')

    def read_fmt(self, fmt):
        size = struct.calcsize(fmt)
        data = self.read_data(size)
        return struct.unpack(fmt, data)[0]

    def read_magic(self):
        # Read magic header:
        magic_len = len(MAGIC_V023)
        magic = self.f.read(magic_len)
        magic = magic.decode('ascii')
        if magic != MAGIC_V023:
            raise ValueError('Unexpected magic value {}'.format(magic))

    def read_u8(self):
        return self.read_fmt('B')

    def read_s8(self):
        return self.read_fmt('b')

    def read_u16(self):
        return self.read_fmt('>H')

    def read_s16(self):
        return self.read_fmt('>h')

    def read_u32(self):
        return self.read_fmt('>I')

    def read_s32(self):
        return self.read_fmt('>i')

    def parse_header(self):
        header = Header()
        magic = self.read_u32()
        if magic == INTEXT_MAGIC_NUMBER_SMALL:
            header.res_len = self.read_u32()
            header.obj_counter = self.read_u32()
            header.size_32 = self.read_u32()
            header.size_64 = self.read_u32()
        elif magic == INTEXT_MAGIC_NUMBER_BIG:
            raise NotImplementedError(str(magic))
        else:  # pragma: no cover
            raise NotImplementedError(str(magic))
        logger.debug(
            'Header: res len=%s, obj_counter=%s',
            header.res_len,
            header.obj_counter
        )
        return header

    def read_data(self, size):
        return self.f.read(size)

    def read_value(self, typ):
        """ Read arbitrary ocaml object.

        An object is stored with a header first, then a marshalled object.
        """
        header = self.parse_header()
        value = self.read_item()
        assert len(value) == len(typ)
        for field, val in zip(typ, value):
            print(field, val)
        return value

    def read_item(self):
        """ Read a single item """
        code = self.read_data(1)[0]
        logger.debug('code %s', hex(code))
        if code >= MarshallCode.PREFIX_SMALL_BLOCK:
            tag = code & 0xf
            size = (code >> 4) & 0x7
            value = self.read_block(tag, size)
        elif code >= MarshallCode.PREFIX_SMALL_INT:
            value = code & 0x3f
            logger.debug('Small int: %s', value)
        elif code >= MarshallCode.PREFIX_SMALL_STRING:
            size = code & 0x1f
            value = self.read_string(size)
        elif code == MarshallCode.CODE_INT8:
            value = self.read_s8()
        elif code == MarshallCode.CODE_INT16:
            value = self.read_s16()
        elif code == MarshallCode.CODE_INT32:
            value = self.read_s32()
        elif code == MarshallCode.CODE_INT64:
            value = self.read_s64()
        elif code == MarshallCode.CODE_SHARED8:
            ofs = self.read_u8()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_SHARED16:
            ofs = self.read_u16()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_SHARED32:
            ofs = self.read_u32()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_BLOCK32:
            header2 = self.read_u32()
            tag = header2 & 0xff
            size = header2 >> 10
            value = self.read_block(tag, size)
        elif code == MarshallCode.CODE_BLOCK64:
            raise NotImplementedError()
        elif code == MarshallCode.CODE_STRING8:
            size = self.read_u8()
            value = self.read_string(size)
        elif code == MarshallCode.CODE_STRING32:
            size = self.read_u32()
            value = self.read_string(size)
        else:
            raise NotImplementedError()
        return value

    def read_shared(self, ofs):
        # TODO: what is this?
        logger.debug('Shared at offset %s', ofs)

    def read_string(self, size):
        logger.debug('String with size %s', size)
        data = self.read_data(size)
        logger.debug('String raw data %s', data)
        # value = data.decode('ascii')
        # logger.debug('String value: "%s"', value)
        value = data
        return value

    def read_block(self, tag, size):
        logger.debug('Reading block with tag %s and size %s', tag, size)
        values = []
        for _ in range(size):
            values.append(self.read_item())
        logger.debug('Completed block %s', values)
        return values

    def olddd(self):
        result = {}
        for field_name, field_type in typ:
            if field_type == 'string':
                data = self.f.read(20)
                print(data)
            else:  # pragma: no cover
                raise NotImplementedError(field_type)
            result[field_name] = value
        return result
