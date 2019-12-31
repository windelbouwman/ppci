""" OCaml marshalling format.

Marshalling as described here:

http://cadmium.x9c.fr/distrib/caml-formats.pdf

"""


import enum
import io
import logging
from .io import FileReader

logger = logging.getLogger("ocaml")


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


INTEXT_MAGIC_NUMBER_SMALL = 0x8495A6BE
INTEXT_MAGIC_NUMBER_BIG = 0x8495A6BF


class Header:
    """ Marshalled data header """

    pass


def parse_header(reader):
    header = Header()
    magic = reader.read_u32()
    if magic == INTEXT_MAGIC_NUMBER_SMALL:
        header.res_len = reader.read_u32()
        header.obj_counter = reader.read_u32()
        header.size_32 = reader.read_u32()
        header.size_64 = reader.read_u32()
    elif magic == INTEXT_MAGIC_NUMBER_BIG:
        raise NotImplementedError(str(magic))
    else:  # pragma: no cover
        raise NotImplementedError(str(magic))
    logger.debug(
        "Header: res len=%s, obj_counter=%s",
        header.res_len,
        header.obj_counter,
    )
    return header


def read_value(reader):
    if isinstance(reader, bytes):
        reader = FileReader(io.BytesIO(reader))

    if not isinstance(reader, FileReader):
        raise TypeError("read_value requires a FileReader or bytes")

    m = Marshall(reader)
    return m.read_item()


class Marshall:
    def __init__(self, reader):
        self.reader = reader
        self._items = []

    def read_item(self):
        """ Read a single item """
        code = self.reader.read_byte()
        logger.debug("code %s", hex(code))
        if code >= MarshallCode.PREFIX_SMALL_BLOCK:
            tag = code & 0xF
            size = (code >> 4) & 0x7
            value = self.read_block(tag, size)
        elif code >= MarshallCode.PREFIX_SMALL_INT:
            value = code & 0x3F
            logger.debug("Small int: %s", value)
        elif code >= MarshallCode.PREFIX_SMALL_STRING:
            size = code & 0x1F
            value = self.read_string(size)
        elif code == MarshallCode.CODE_INT8:
            value = self.reader.read_s8()
        elif code == MarshallCode.CODE_INT16:
            value = self.reader.read_s16()
        elif code == MarshallCode.CODE_INT32:
            value = self.reader.read_s32()
        elif code == MarshallCode.CODE_INT64:
            value = self.reader.read_s64()
        elif code == MarshallCode.CODE_SHARED8:
            ofs = self.reader.read_u8()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_SHARED16:
            ofs = self.reader.read_u16()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_SHARED32:
            ofs = self.reader.read_u32()
            value = self.read_shared(ofs)
        elif code == MarshallCode.CODE_BLOCK32:
            header2 = self.reader.read_u32()
            tag = header2 & 0xFF
            size = header2 >> 10
            value = self.read_block(tag, size)
        elif code == MarshallCode.CODE_BLOCK64:
            raise NotImplementedError()
        elif code == MarshallCode.CODE_STRING8:
            size = self.reader.read_u8()
            value = self.read_string(size)
        elif code == MarshallCode.CODE_STRING32:
            size = self.reader.read_u32()
            value = self.read_string(size)
        else:
            raise NotImplementedError()

        # Store for share usage:
        self._items.append(value)
        return value

    def read_shared(self, ofs):
        """ Read a shared value.

        Offset is an index back into an already deserialized object.
        0 means the last object, 1 the preceding object, etc..
        """
        logger.debug("Shared at offset %s", ofs)
        return self._items[-1 - ofs]

    def read_string(self, size):
        """ Read string data of length given by size """
        logger.debug("String with size %s", size)
        data = self.reader.read_data(size)
        logger.debug("String raw data %s", data)
        # value = data.decode('ascii')
        # logger.debug('String value: "%s"', value)
        value = data
        return value

    def read_block(self, tag, size):
        """ A series of data with a tag """
        logger.debug("Reading block with tag %s and size %s", tag, size)
        values = []
        for _ in range(size):
            values.append(self.read_item())
        logger.debug("Completed block %s", values)
        return values
