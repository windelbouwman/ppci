
"""
Object files are used to store assembled code. Information contained
is code, symbol table and relocation information.
"""

import json
import binascii
from .. import CompilerError, make_num


class Symbol:
    def __init__(self, name, value, section):
        self.name = name
        self.value = value
        self.section = section

    def __repr__(self):
        return 'SYM {}, val={} sec={}'.format(self.name, self.value, self.section)

    def __eq__(self, other):
        return (self.name, self.value, self.section) == \
            (other.name, other.value, other.section)


class Relocation:
    """ Represents a relocation entry. A relocation always has a symbol to refer to
     and a relocation type """
    def __init__(self, sym, offset, typ, section):
        self.sym = sym
        self.offset = offset
        self.typ = typ
        self.section = section

    def __repr__(self):
        return 'RELOC {} off={} t={} sec={}'.format(self.sym, self.offset, self.typ, self.section)

    def __eq__(self, other):
        return (self.sym, self.offset, self.typ, self.section) ==\
            (other.sym, other.offset, other.typ, other.section)


class Section:
    def __init__(self, name):
        self.name = name
        self.address = 0
        self.data = bytearray()

    def add_data(self, data):
        self.data += data

    @property
    def Size(self):
        return len(self.data)

    def __repr__(self):
        return 'SECTION {}'.format(self.name)

    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address) \
            and (self.data == other.data)


class Image:
    def __init__(self, location, data=bytes()):
        self.location = location
        self.data = data

    def __eq__(self, other):
        return (self.location == other.location) \
            and (self.data == other.data)

    @property
    def size(self):
        return len(self.data)


class ObjectFile:
    """ Container for sections with compiled code or data.
        Also contains symbols and relocation entries """
    def __init__(self):
        self.symbols = {}
        self.sections = {}
        self.relocations = []
        self.images = {}

    def find_symbol(self, name):
        return self.symbols[name]

    def add_symbol(self, name, value, section):
        if name in self.symbols:
            raise CompilerError('{} already defined'.format(name))
        assert section in self.sections
        sym = Symbol(name, value, section)
        self.symbols[name] = sym
        return sym

    def add_relocation(self, sym_name, offset, typ, section):
        assert type(sym_name) is str, str(sym_name)
        assert section in self.sections
        # assert sym_name in self.symbols
        reloc = Relocation(sym_name, offset, typ, section)
        self.relocations.append(reloc)
        return reloc

    def get_section(self, name):
        if name not in self.sections:
            self.sections[name] = Section(name)
        return self.sections[name]

    def get_image(self, name):
        return self.images[name]

    def add_image(self, name, location, data):
        img = Image(location, data)
        self.images[name] = img

    def get_symbol_value(self, name):
        symbol = self.find_symbol(name)
        section = self.get_section(symbol.section)
        return symbol.value + section.address

    def __repr__(self):
        return 'CodeObject of {} bytes'.format(self.byte_size)

    @property
    def byte_size(self):
        return sum(len(image.data) for image in self.sections.values())

    def __eq__(self, other):
        return (self.symbols == other.symbols) and \
            (self.sections == other.sections) and \
            (self.relocations == other.relocations) and \
            (self.images == other.images)

    def save(self, f):
        save_object(self, f)


def save_object(o, f):
    json.dump(serialize(o), f, indent=2, sort_keys=True)


def load_object(f):
    return deserialize(json.load(f))


def bin2asc(data):
    return binascii.hexlify(data).decode('ascii')


def asc2bin(data):
    return bytearray(binascii.unhexlify(data.encode('ascii')))


def serialize(x):
    res = {}
    if isinstance(x, ObjectFile):
        res['sections'] = []
        for sname in sorted(x.sections.keys()):
            s = x.sections[sname]
            res['sections'].append(serialize(s))
        res['symbols'] = []
        for sname in sorted(x.symbols.keys()):
            s = x.symbols[sname]
            res['symbols'].append(serialize(s))
        res['relocations'] = []
        for reloc in x.relocations:
            res['relocations'].append(serialize(reloc))
        res['images'] = {}
        for image_name in x.images:
            res['images'][image_name] = serialize(x.images[image_name])
    elif isinstance(x, Image):
        res['data'] = bin2asc(x.data)
        res['location'] = x.location
    elif isinstance(x, Section):
        res['name'] = x.name
        res['address'] = hex(x.address)
        res['data'] = bin2asc(x.data)
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
    obj = ObjectFile()
    for section in d['sections']:
        so = obj.get_section(section['name'])
        so.address = make_num(section['address'])
        so.data = asc2bin(section['data'])
    for reloc in d['relocations']:
        obj.add_relocation(
            reloc['symbol'], make_num(reloc['offset']),
            reloc['type'], reloc['section'])
    for sym in d['symbols']:
        obj.add_symbol(sym['name'], make_num(sym['value']), sym['section'])
    for image_name in d['images']:
        image = d['images'][image_name]
        obj.add_image(image_name, image['location'], asc2bin(image['data']))
    return obj
