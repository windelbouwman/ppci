import struct
import binascii


DATA = 0
EOF = 1
EXTLINADR = 4
STARTADDR = 5


class HexFileException(Exception):
    pass


def parse_hex_line(line):
    """ Parses a hexfile line into three parts """
    # Remove ':'
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
    return (address, typ, data)


def make_hex_line(address, typ, data=bytes()):
    """ Create an ascii hex line out of data, address and record type """
    bytecount = len(data)
    nums = bytearray()
    nums.append(bytecount)
    nums.extend(struct.pack('>H', address))
    nums.append(typ)
    nums.extend(data)
    crc = sum(nums)
    crc = ((~crc) + 1) & 0xFF
    nums.append(crc)
    line = ':' + binascii.hexlify(nums).decode('ascii')
    return line


def chunks(data, csize=16):
    idx = 0
    while idx < len(data):
        s = min(len(data) - idx, csize)
        yield data[idx:idx+s]
        idx += s


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
        yield parse_hex_line(line)


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
        for address, typ, data in hexfields(open_file):
            if end_of_file:
                raise HexFileException('hexfile line after end of file record')
            if typ == DATA:
                self.add_region(address + ext, data)
            elif typ == EXTLINADR:
                ext = (struct.unpack('>H', data[0:2])[0]) << 16
            elif typ == EOF:
                if len(data) != 0:
                    raise HexFileException('end of file not empty')
                end_of_file = True
            elif typ == STARTADDR:
                self.start_address = struct.unpack('>I', data[0:4])[0]
            else:  # pragma: no cover
                raise NotImplementedError(
                    'record type {0} not implemented'.format(typ))
        return self

    def __repr__(self):
        size = sum(r.Size for r in self.regions)
        return 'Hexfile containing {} bytes'.format(size)

    def dump(self, contents=False):
        print(self)
        for region in self.regions:
            print(region)
            print(binascii.hexlify(region.data))

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
                if r1.EndAddress == r2.address:
                    r1.addData(r2.data)
                    self.regions.remove(r2)
                    change = True
                elif r1.EndAddress > r2.address:
                    raise HexFileException('Overlapping regions')

    def merge(self, other):
        for region in other.regions:
            self.add_region(region.address, region.data)

    def write_hex_line(self, address, typ, data=bytes()):
        """ Write a single hexfile line """
        print(make_hex_line(address, typ, data), file=self.f)

    def save(self, f):
        """ Save hexfile to file-like object """
        self.f = f
        for r in self.regions:
            ext = r.address & 0xFFFF0000
            self.write_hex_line(0, EXTLINADR, struct.pack('>H', ext >> 16))
            address = r.address - ext
            for chunk in chunks(r.data):
                if address >= 0x10000:
                    ext += 0x10000
                    self.write_hex_line(
                        0, EXTLINADR, struct.pack('>H', ext >> 16))
                    address -= 0x10000
                self.write_hex_line(address, DATA, chunk)
                address += len(chunk)
        self.write_hex_line(0, EOF)


class HexFileRegion:
    def __init__(self, address, data=bytes()):
        self.address = address
        self.data = data

    def __repr__(self):
        return 'Region at 0x{:08X} of {} bytes'.format(
            self.address, len(self.data))

    def __eq__(self, other):
        return (self.address, self.data) == (other.address, other.data)

    def addData(self, d):
        self.data = self.data + d

    @property
    def Size(self):
        return len(self.data)

    @property
    def EndAddress(self):
        return self.address + len(self.data)
