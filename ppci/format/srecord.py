""" Motorola s-record format.

https://en.wikipedia.org/wiki/SREC_(file_format)
"""

import binascii
from ..utils.bitfun import value_to_bytes_big_endian
from ..utils.hexdump import chunks


class SRecord:
    address_byte_sizes = {0: 2, 1: 2, 2: 3, 3: 4, 5: 2, 6: 3, 7: 4, 8: 3, 9: 2}

    def __init__(self, typ, address, data):
        self.typ = typ
        if typ not in self.address_byte_sizes:
            raise ValueError("Invalid s-record type {}".format(typ))
        self.address = address
        self.data = data

    def to_line(self) -> str:
        addr_size = self.address_byte_sizes[self.typ]
        addr_data = value_to_bytes_big_endian(self.address, addr_size)
        data = addr_data + self.data

        # Add count:
        count = len(data) + 1
        data = bytes([count]) + data

        # Add crc:
        crc = sum(data)
        crc = (~crc) & 0xFF
        data += bytes([crc])
        txt_data = binascii.hexlify(data).decode("ascii").upper()
        line = "S{}{}".format(self.typ, txt_data)
        return line


def write_srecord(obj, f):
    """ Write object to srecord """
    data = obj.get_section("code").data
    record = SRecord(1, 0, b"HDR")
    print(record.to_line(), file=f)
    address = 0
    for chunk in chunks(data):
        record = SRecord(1, address, chunk)
        print(record.to_line(), file=f)
        address += len(chunk)
    record = SRecord(9, 0, bytes())
    print(record.to_line(), file=f)
