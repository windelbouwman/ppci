""" Module to work with intel hex files.

This module can be used to work with intel hexfiles.

"""

import struct
import binascii
from ..utils.hexdump import hexdump, chunks


DATA = 0
EOF = 1
EXTLINADR = 4
STARTADDR = 5


class HexFileException(Exception):
    """ Exception raised when hexfile handling fails """
    pass


class HexLine:
    """ A single line in a hexfile """
    def __init__(self, address, typ, data=bytes()):
        self.address = address
        self.typ = typ
        self.data = data

    @classmethod
    def from_line(cls, line: str):
        """ Parses a hexfile line into three parts """
        # Remove ':'
        if line[0] != ':':
            raise ValueError('Expect hexline to start with :')
        line = line[1:]

        nums = bytes.fromhex(line)
        bytecount = nums[0]
        if len(nums) != bytecount + 5:
            raise HexFileException('byte count field incorrect')
        crc = sum(nums)
        if (crc & 0xFF) != 0:
            raise HexFileException('crc incorrect')
        address = struct.unpack('>H', nums[1:3])[0]
        typ = nums[3]
        data = nums[4:-1]
        return cls(address, typ, data)

    def to_line(self) -> str:
        """ Create an ascii hex line """
        bytecount = len(self.data)
        nums = bytearray()
        nums.append(bytecount)
        nums.extend(struct.pack('>H', self.address))
        nums.append(self.typ)
        nums.extend(self.data)
        crc = sum(nums)
        crc = ((~crc) + 1) & 0xFF
        nums.append(crc)
        line = ':' + binascii.hexlify(nums).decode('ascii')
        return line


def hexfields(f):
    for line in f:
        # Strip spaces and newlines:
        line = line.strip()

        if not line:
            # Skip empty lines
            continue

        if line[0] != ':':
            # Skip lines that do not start with a ':'
            continue
        yield HexLine.from_line(line)


class HexFile:
    """ Represents an intel hexfile """
    def __init__(self):
        self.regions = []
        self.start_address = 0

    @staticmethod
    def load(open_file):
        """ Load a hexfile from file """
        self = HexFile()
        end_of_file = False
        ext = 0
        for line in hexfields(open_file):
            if end_of_file:
                raise HexFileException('hexfile line after end of file record')

            if line.typ == DATA:
                self.add_region(line.address + ext, line.data)
            elif line.typ == EXTLINADR:
                ext = (struct.unpack('>H', line.data[0:2])[0]) << 16
            elif line.typ == EOF:
                if len(line.data) != 0:
                    raise HexFileException('end of file not empty')
                end_of_file = True
            elif line.typ == STARTADDR:
                self.start_address = struct.unpack('>I', line.data[0:4])[0]
            else:  # pragma: no cover
                raise NotImplementedError(
                    'record type {0} not implemented'.format(line.typ))
        return self

    def __repr__(self):
        size = sum(r.size for r in self.regions)
        return 'Hexfile containing {} bytes'.format(size)

    def dump(self, contents=False):
        """ Print info about this hexfile """
        print(self)
        for region in self.regions:
            print(region)
            hexdump(region.data, address=region.address)

    def __eq__(self, other):
        regions = self.regions
        oregions = other.regions
        if len(regions) != len(oregions):
            return False
        return all(rs == ro for rs, ro in zip(regions, oregions))

    def add_region(self, address, data):
        """ Add a chunk of data at the given address """
        region = HexFileRegion(address, data)
        self.regions.append(region)
        self.check()

    def check(self):
        self.regions.sort(key=lambda r: r.address)
        change = True
        while change and len(self.regions) > 1:
            change = False
            for r1, r2 in zip(self.regions[:-1], self.regions[1:]):
                if r1.end_address == r2.address:
                    r1.add_data(r2.data)
                    self.regions.remove(r2)
                    change = True
                elif r1.end_address > r2.address:
                    raise HexFileException('Overlapping regions')

    def merge(self, other):
        for region in other.regions:
            self.add_region(region.address, region.data)

    def write_hex_line(self, line):
        """ Write a single hexfile line """
        print(line.to_line(), file=self.f)

    def save(self, f):
        """ Save hexfile to file-like object """
        self.f = f
        for region in self.regions:
            ext = region.address & 0xFFFF0000
            self.write_hex_line(
                HexLine(0, EXTLINADR, struct.pack('>H', ext >> 16)))
            address = region.address - ext
            for chunk in chunks(region.data):
                if address >= 0x10000:
                    ext += 0x10000
                    self.write_hex_line(
                        HexLine(0, EXTLINADR, struct.pack('>H', ext >> 16)))
                    address -= 0x10000
                self.write_hex_line(HexLine(address, DATA, chunk))
                address += len(chunk)
        self.write_hex_line(HexLine(0, EOF))


class HexFileRegion:
    """ A continuous region of data starting at some address """
    def __init__(self, address, data=bytes()):
        self.address = address
        self.data = data

    def __repr__(self):
        return 'Region at 0x{:08X} of {} bytes'.format(
            self.address, len(self.data))

    def __eq__(self, other):
        return (self.address, self.data) == (other.address, other.data)

    def add_data(self, data):
        """ Add data to this region """
        self.data = self.data + data

    @property
    def size(self):
        """ The size of this region """
        return len(self.data)

    @property
    def end_address(self):
        """ End address for this region """
        return self.address + len(self.data)
