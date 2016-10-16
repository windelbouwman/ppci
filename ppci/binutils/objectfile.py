
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
- debug data have an offset into a section and contain data.

- sections cannot overlap
"""

import json
import binascii
from ..common import CompilerError, make_num
from ..arch.encoding import Relocation
from . import debuginfo


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
        return 'SECTION {} size=0x{:x} address=0x{:x}'.format(
            self.name, self.size, self.address)

    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address) \
            and (self.data == other.data) and \
            (self.alignment == other.alignment)

    def __hash__(self):
        return id(self)


class Image:
    """ Memory image.

    A memory image is a piece that can be loaded into memory.
    """
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
        """ Add a section to this memory image """
        self.sections.append(section)


def merge_memories(mem1, mem2, name):
    """ Merge two memories into a new one """
    # TODO: pick location based on address?
    location = mem1.location
    mem3 = Image(name, location)
    for section in mem1.sections:
        mem3.add_section(section)
    for section in mem2.sections:
        mem3.add_section(section)
    return mem3


class ObjectFile:
    """ Container for sections with compiled code or data.
        Also contains symbols and relocation entries.
        Also contains debug information.
    """
    def __init__(self, arch):
        self.symbols = []
        self.symbol_map = {}
        self.sections = []
        self.section_map = {}
        self.relocations = []
        self.images = []
        self.image_map = {}
        self.debug_info = None
        self.arch = arch

    def __repr__(self):
        return 'CodeObject of {} bytes'.format(self.byte_size)

    def has_symbol(self, name):
        """ Check if this object file has a symbol with name 'name' """
        return name in self.symbol_map

    def get_symbol(self, name):
        """ Get a symbol """
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

    def get_symbol_value(self, name):
        """ Lookup a symbol and determine its value """
        symbol = self.get_symbol(name)
        section = self.get_section(symbol.section)
        return symbol.value + section.address

    def del_symbol(self, name):
        """ Remove a symbol with a given name """
        sym = self.symbol_map.pop(name)
        self.symbols.remove(sym)

    def add_relocation(self, reloc):
        """ Add a relocation entry """
        assert isinstance(reloc, Relocation)
        assert isinstance(reloc.symbol_name, str), str(reloc.symbol_name)
        assert self.has_section(reloc.section)
        # assert sym_name in self.symbols
        self.relocations.append(reloc)
        return reloc

    def gen_relocation(self, typ, sym_name, offset=0, section=None, addend=0):
        """ Create a relocation given by name """
        reloc_cls = self.arch.isa.relocation_map['rel8']
        reloc = reloc_cls(
            sym_name, offset=offset, section=section, addend=addend)
        return self.add_relocation(reloc)

#    def add_debug(self, section, offset, data):
#        """ Add debug data to this object file """
#        assert self.has_section(section)
#        debug = Debug(section, offset, data)
#        self.debug.append(debug)

    def has_section(self, name):
        """ Check if the object file has a section with the given name """
        return name in self.section_map

    def add_section(self, section):
        """ Add a section """
        self.sections.append(section)
        self.section_map[section.name] = section

    def get_section(self, name, create=False):
        """ Get or create a section with the given name """
        if (not self.has_section(name)) and create:
            self.add_section(Section(name))
        return self.section_map[name]

    def get_image(self, name):
        """ Get a memory image """
        return self.image_map[name]

    def add_image(self, image):
        """ Add an image """
        self.images.append(image)
        self.image_map[image.name] = image

    @property
    def byte_size(self):
        """ Get the size in bytes of this object file """
        return sum(section.size for section in self.sections)

    def __eq__(self, other):
        return (self.symbols == other.symbols) and \
            (self.sections == other.sections) and \
            (self.relocations == other.relocations) and \
            (self.images == other.images)

    def save(self, output_file):
        """ Save object file to a file like object """
        self.polish()
        json.dump(serialize(self), output_file, indent=2, sort_keys=True)
        print(file=output_file)

    @staticmethod
    def load(input_file):
        """ Load object file from file """
        return deserialize(json.load(input_file))

    def polish(self):
        """ Cleanup an object file """
        if self.debug_info:
            # TODO: move this to linker?
            # fix debug info objects:
            def fx(x):
                if isinstance(x, str):
                    sym = self.get_symbol(x)
                    return debuginfo.DebugAddress(sym.section, sym.value)
                else:
                    # assert isinstance(x, debuginfo.DebugAddress)
                    return x
            for loc in self.debug_info.locations:
                loc.address = fx(loc.address)
            for func in self.debug_info.functions:
                func.begin = fx(func.begin)
                func.end = fx(func.end)
            for var in self.debug_info.variables:
                var.address = fx(var.address)

        # remove local labels:
        names = [s.name for s in self.symbols if s.name.startswith('.L')]
        for name in names:
            self.del_symbol(name)


def print_object(obj):
    """ Display an object in a user friendly manner """
    print(obj)
    for section in obj.sections:
        print(section)
    for symbol in obj.symbols:
        print(symbol)
    for reloc in obj.relocations:
        print(reloc)


def chunks(data, size=30):
    """ Split iterable thing into n-sized chunks """
    for i in range(0, len(data), size):
        yield data[i:i+size]


def bin2asc(data):
    """ Encode binary data as ascii. If it is a large data set, then use a
        list of hex characters.
    """
    if len(data) > 30:
        res = []
        for part in chunks(data):
            res.append(binascii.hexlify(part).decode('ascii'))
        return res
    else:
        return binascii.hexlify(data).decode('ascii')


def asc2bin(data):
    """ Decode ascii into binary """
    if isinstance(data, str):
        return bytearray(binascii.unhexlify(data.encode('ascii')))
    elif isinstance(data, list):
        res = bytearray()
        for part in data:
            res.extend(binascii.unhexlify(part.encode('ascii')))
        return res
    else:  # pragma: no cover
        raise NotImplementedError(str(type(data)))


def serialize(x):
    """ Serialize an object so it can be json-ified, or serialized """
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
        if x.debug_info:
            res['debug'] = debuginfo.serialize(x.debug_info)
        res['arch'] = x.arch.make_id_str()
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
        res['symbol'] = x.symbol_name
        res['offset'] = hex(x.offset)
        res['type'] = x.name
        res['section'] = x.section
    else:  # pragma: no cover
        raise NotImplementedError(str(type(x)))
    return res


def deserialize(data):
    """ Create an object file from dict-like data """
    from ..api import get_arch
    arch = get_arch(data['arch'])
    obj = ObjectFile(arch)
    for section in data['sections']:
        section_object = Section(section['name'])
        obj.add_section(section_object)
        section_object.address = make_num(section['address'])
        section_object.data = asc2bin(section['data'])
        section_object.alignment = make_num(section['alignment'])
    for reloc in data['relocations']:
        typ = reloc['type']
        rcls = arch.isa.relocation_map[typ]
        r = rcls(
            reloc['symbol'],
            offset=make_num(reloc['offset']),
            section=reloc['section'],
            addend=0)
        obj.add_relocation(r)
    for sym in data['symbols']:
        obj.add_symbol(sym['name'], make_num(sym['value']), sym['section'])
    for image in data['images']:
        img = Image(image['name'], make_num(image['location']))
        obj.add_image(img)
        for section_name in image['sections']:
            assert obj.has_section(section_name)
            img.add_section(obj.get_section(section_name))
    if 'debug' in data:
        obj.debug_info = debuginfo.deserialize(data['debug'])
    return obj
