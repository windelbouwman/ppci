
"""
Object files are used to store assembled code. Information contained
is code, symbol table and relocation information.

The hierarchy is as follows:
- an object file contains zero or more sections.
- an object file may contains memory definitions, which contain a sequence
  of contained sections.
- a section contains a name and data.
- relocations are offset into a section, refer a symbol and have a type
- symbols are offset into a section and have a name

- sections cannot overlap
"""

import json
import binascii
from ..common import CompilerError, make_num


class Symbol:
    """ A symbol definition in an object file """
    def __init__(self, name, value, section):
        self.name = name
        self.value = value
        self.section = section

    def __repr__(self):
        return 'Symbol({}, val={} section={})'.format(
            self.name, self.value, self.section)

    def __eq__(self, other):
        return (self.name, self.value, self.section) == \
            (other.name, other.value, other.section)


class Relocation:
    """ Represents a relocation entry. A relocation always has a symbol to
        refer to and a relocation type """
    def __init__(self, sym, offset, typ, section):
        self.sym = sym
        self.offset = offset
        self.typ = typ
        self.section = section

    def __repr__(self):
        return 'RELOC {} off={} t={} sec={}'.format(
            self.sym, self.offset, self.typ, self.section)

    def __eq__(self, other):
        return (self.sym, self.offset, self.typ, self.section) ==\
            (other.sym, other.offset, other.typ, other.section)


class Section:
    """ A defined region of data in the object file """
    def __init__(self, name):
        self.name = name
        self.address = 0
        self.alignment = 4
        self.data = bytearray()

    def add_data(self, data):
        """ Append data to the end of this section """
        self.data += data

    @property
    def size(self):
        return len(self.data)

    def __repr__(self):
        return 'SECTION {} {} {}'.format(self.name, self.size, self.address)

    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address) \
            and (self.data == other.data) and \
            (self.alignment == other.alignment)

    def __hash__(self):
        return id(self)


class Image:
    def __init__(self, name, location):
        self.location = location
        self.name = name
        self.sections = []

    def __eq__(self, other):
        return (self.location == other.location) \
            and (self.sections == other.sections) \
            and (self.name == other.name)

    def __repr__(self):
        return 'IMG {} {} 0x{:08X}'.format(self.name, self.size, self.location)

    def __hash__(self):
        return id(self)

    @property
    def data(self):
        """ Get the data of this memory """
        data = bytearray()
        current_address = self.location
        for section in self.sections:
            if section.address < current_address:
                raise ValueError('sections overlap!!')
            if section.address > current_address:
                delta = section.address - current_address
                data += bytes([0] * delta)
                current_address += delta
            assert section.address == current_address
            data += section.data
            current_address += section.size
        return data

    @property
    def size(self):
        """ Determine the size of this memory """
        return len(self.data)

    def add_section(self, section):
        self.sections.append(section)


def merge_memories(mem1, mem2, name):
    """ Merge two memories into a new one """
    # TODO: pick location based on address?
    location = mem1.location
    mem3 = Image(name, location)
    for s in mem1.sections:
        mem3.add_section(s)
    for s in mem2.sections:
        mem3.add_section(s)
    return mem3


class ObjectFile:
    """ Container for sections with compiled code or data.
        Also contains symbols and relocation entries """
    def __init__(self):
        self.symbols = []
        self.symbol_map = {}
        self.sections = []
        self.section_map = {}
        self.relocations = []
        self.images = []
        self.image_map = {}

    def has_symbol(self, name):
        return name in self.symbol_map

    def find_symbol(self, name):
        return self.symbol_map[name]

    def add_symbol(self, name, value, section):
        """ Define a new symbol """
        if self.has_symbol(name):
            raise CompilerError('{} already defined'.format(name))
        assert self.has_section(section)
        sym = Symbol(name, value, section)
        self.symbol_map[name] = sym
        self.symbols.append(sym)
        return sym

    def add_relocation(self, sym_name, offset, typ, section):
        """ Add a relocation """
        assert type(sym_name) is str, str(sym_name)
        assert self.has_section(section)
        # assert sym_name in self.symbols
        reloc = Relocation(sym_name, offset, typ, section)
        self.relocations.append(reloc)
        return reloc

    def has_section(self, name):
        """ Check if the object file has a section with the given name """
        return name in self.section_map

    def add_section(self, section):
        """ Add a section """
        self.sections.append(section)
        self.section_map[section.name] = section

    def get_section(self, name):
        """ Get or create a section with the given name """
        if not self.has_section(name):
            self.add_section(Section(name))
        return self.section_map[name]

    def get_image(self, name):
        return self.image_map[name]

    def add_image(self, image):
        self.images.append(image)
        self.image_map[image.name] = image

    def get_symbol_value(self, name):
        """ Lookup a symbol and determine its value """
        symbol = self.find_symbol(name)
        section = self.get_section(symbol.section)
        return symbol.value + section.address

    def __repr__(self):
        return 'CodeObject of {} bytes'.format(self.byte_size)

    @property
    def byte_size(self):
        return sum(section.size for section in self.sections)

    def __eq__(self, other):
        return (self.symbols == other.symbols) and \
            (self.sections == other.sections) and \
            (self.relocations == other.relocations) and \
            (self.images == other.images)

    def save(self, f):
        """ Save object file to a file like object """
        save_object(self, f)


def save_object(obj, f):
    json.dump(serialize(obj), f, indent=2, sort_keys=True)


def load_object(f):
    """ Load object file from file """
    return deserialize(json.load(f))


def print_object(obj):
    print(obj)
    for section in obj.sections:
        print(section)
    for symbol in obj.symbols:
        print(symbol)
    for reloc in obj.relocations:
        print(reloc)


def bin2asc(data):
    """ Encode binary data as ascii """
    return binascii.hexlify(data).decode('ascii')


def asc2bin(data):
    """ Decode ascii into binary """
    return bytearray(binascii.unhexlify(data.encode('ascii')))


def serialize(x):
    """ Serialize an object so it can be json-ified """
    res = {}
    if isinstance(x, ObjectFile):
        res['sections'] = []
        for section in x.sections:
            res['sections'].append(serialize(section))
        res['symbols'] = []
        for symbol in x.symbols:
            res['symbols'].append(serialize(symbol))
        res['relocations'] = []
        for reloc in x.relocations:
            res['relocations'].append(serialize(reloc))
        res['images'] = []
        for image in x.images:
            res['images'].append(serialize(image))
    elif isinstance(x, Image):
        res['name'] = x.name
        res['location'] = hex(x.location)
        res['sections'] = []
        for section in x.sections:
            res['sections'].append(section.name)
    elif isinstance(x, Section):
        res['name'] = x.name
        res['address'] = hex(x.address)
        res['data'] = bin2asc(x.data)
        res['alignment'] = hex(x.alignment)
    elif isinstance(x, Symbol):
        res['name'] = x.name
        res['value'] = hex(x.value)
        res['section'] = x.section
    elif isinstance(x, Relocation):
        res['symbol'] = x.sym
        res['offset'] = hex(x.offset)
        res['type'] = x.typ
        res['section'] = x.section
    return res


def deserialize(d):
    """ Create an object file from data """
    obj = ObjectFile()
    for section in d['sections']:
        so = Section(section['name'])
        obj.add_section(so)
        so.address = make_num(section['address'])
        so.data = asc2bin(section['data'])
        so.alignment = make_num(section['alignment'])
    for reloc in d['relocations']:
        obj.add_relocation(
            reloc['symbol'], make_num(reloc['offset']),
            reloc['type'], reloc['section'])
    for sym in d['symbols']:
        obj.add_symbol(sym['name'], make_num(sym['value']), sym['section'])
    for image in d['images']:
        img = Image(image['name'], make_num(image['location']))
        obj.add_image(img)
        for section_name in image['sections']:
            assert obj.has_section(section_name)
            img.add_section(obj.get_section(section_name))
    return obj
