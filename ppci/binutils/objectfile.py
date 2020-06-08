""" Object files are used to store assembled code.

Information contained
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
from ..common import CompilerError, make_num, get_file
from ..utils.binary_txt import bin2asc, asc2bin
from . import debuginfo


def get_object(obj):
    """ Try hard to load an object """
    if not isinstance(obj, ObjectFile):
        f = get_file(obj)
        obj = ObjectFile.load(f)
        f.close()
    return obj


class Symbol:
    """ A symbol definition in an object file """

    def __init__(self, id, name, binding, value, section, typ, size):
        assert isinstance(id, int)
        self.id = id
        self.name = name
        self.binding = binding
        self.value = value
        self.section = section
        self.typ = typ
        self.size = size

    @property
    def undefined(self):
        """ Test if this symbol is undefined. """
        return self.value is None

    @property
    def defined(self):
        return not self.undefined

    @property
    def is_global(self):
        return self.binding == "global"

    @property
    def is_function(self):
        """ Test if this symbol is a function. """
        return self.typ == "func"

    def __repr__(self):
        return "Symbol({}, binding={}, val={} section={} typ={} size={})".format(
            self.name,
            self.binding,
            self.value,
            self.section,
            self.typ,
            self.size,
        )

    def __eq__(self, other):
        return (
            (self.id == other.id)
            and (self.name == other.name)
            and (self.binding == other.binding)
            and (self.value == other.value)
            and (self.section == other.section)
            and (self.typ == other.typ)
            and (self.size == other.size)
        )


class RelocationEntry:
    """ A relocation entry.

    While it mich be confusing to have Relocation here, and
    RelocationType in arch.encoding, this is cleaner, since the relocation
    here is a record indicating a relocation, while the relocation type
    is emitted by instructions and can actually apply the relocation.


    This class is a record holding information on where to a apply which
    relocation. Not how to do the actual relocation.
    """

    def __init__(self, reloc_type, symbol_id, section, offset, addend):
        self.reloc_type = reloc_type
        self.symbol_id = symbol_id
        self.section = section
        self.offset = offset
        self.addend = addend

    def __eq__(self, other):
        return (
            (self.reloc_type == other.reloc_type)
            and (self.symbol_id == other.symbol_id)
            and (self.section == other.section)
            and (self.offset == other.offset)
            and (self.addend == other.addend)
        )


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
        return "SECTION {} size=0x{:x} address=0x{:x}".format(
            self.name, self.size, self.address
        )

    def __eq__(self, other):
        return (
            (self.name == other.name)
            and (self.address == other.address)
            and (self.data == other.data)
            and (self.alignment == other.alignment)
        )

    def __hash__(self):
        return id(self)


class Image:
    """ Memory image.

    A memory image is a piece that can be loaded into memory.
    """

    def __init__(self, name: str, address: int):
        self.address = address
        self.name = name
        self.sections = []

    def __eq__(self, other):
        return (
            (self.address == other.address)
            and (self.sections == other.sections)
            and (self.name == other.name)
        )

    def __repr__(self):
        return "IMG {} {} 0x{:08X}".format(self.name, self.size, self.address)

    def __str__(self):
        return "Image {} of {} bytes at 0x{:X}".format(
            self.name, self.size, self.address
        )

    def __hash__(self):
        return id(self)

    @property
    def data(self):
        """ Get the data of this memory """
        data = bytearray()
        current_address = self.address
        for section in self.sections:
            if section.address < current_address:
                raise ValueError("sections overlap!!")
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
    address = mem1.address
    mem3 = Image(name, address)
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
        self.symbols_by_id = {}
        self.sections = []
        self.section_map = {}
        self.relocations = []
        self.images = []
        self.image_map = {}
        self.debug_info = None
        self.arch = arch
        self.entry_symbol_id = None  # object file entry point

    def __repr__(self):
        return "CodeObject of {} bytes".format(self.byte_size)

    @property
    def is_executable(self):
        """ Test if this object file is executable by checking the
        entry point.
        """
        return self.entry_symbol_id is not None

    def has_symbol(self, name):
        """ Check if this object file has a symbol with name 'name' """
        return name in self.symbol_map

    def get_symbol(self, name):
        """ Get a symbol """
        return self.symbol_map[name]

    def add_symbol(self, id, name, binding, value, section, typ, size):
        """ Define a new symbol """
        # assert self.has_section(section)
        symbol = Symbol(id, name, binding, value, section, typ, size)
        self.symbols.append(symbol)

        # If the symbol has a global binding, its name must be unique:
        if binding == "global":
            if self.has_symbol(name):
                raise CompilerError("{} already defined".format(name))
            self.symbol_map[name] = symbol

        assert id not in self.symbols_by_id
        self.symbols_by_id[id] = symbol
        return symbol

    def get_symbol_value(self, symbol_name):
        symbol = self.get_symbol(symbol_name)
        return self.get_symbol_id_value(symbol.id)

    def get_symbol_id_value(self, symbol_id):
        """ Lookup a symbol and determine its value """
        symbol = self.symbols_by_id[symbol_id]
        if symbol.undefined:
            raise ValueError("Undefined reference {}".format(symbol.name))

        if symbol.section is None:
            return symbol.value
        else:
            section = self.get_section(symbol.section)
            return symbol.value + section.address

    def del_symbol(self, name):
        """ Remove a symbol with a given name """
        sym = self.symbol_map.pop(name)
        self.symbols.remove(sym)

    def get_undefined_symbols(self):
        """ Get a list of undefined symbols. """
        undefined_symbols = [
            s.name for s in self.symbols if (s.undefined and s.is_global)
        ]
        return undefined_symbols

    def get_defined_symbols(self):
        """ Get a list of defined symbols. """
        defined_symbols = [
            s.name for s in self.symbols if (s.defined and s.is_global)
        ]
        return defined_symbols

    def add_relocation(self, reloc):
        """ Add a relocation entry """
        assert isinstance(reloc, RelocationEntry)
        assert isinstance(reloc.symbol_id, int)
        assert self.has_section(reloc.section)
        self.relocations.append(reloc)
        return reloc

    def gen_relocation(self, reloc_type, symbol_id, section, offset):
        reloc = RelocationEntry(reloc_type, symbol_id, section, offset, 0)
        self.add_relocation(reloc)

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

    def create_section(self, name):
        """ Create and add a section with the given name. """
        if name in self.section_map:
            raise ValueError("section {} already exists!".format(name))
        section = Section(name)
        self.add_section(section)
        return section

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
        return (
            (self.symbols == other.symbols)
            and (self.sections == other.sections)
            and (self.relocations == other.relocations)
            and (self.images == other.images)
        )

    def serialize(self):
        """ Serialize the object into a dictionary structure suitable for json.
        """
        return serialize(self)

    def save(self, output_file):
        """ Save object file to a file like object """
        json.dump(self.serialize(), output_file, indent=2, sort_keys=True)
        print(file=output_file)

    @staticmethod
    def load(input_file):
        """ Load object file from file """
        return deserialize(json.load(input_file))


def print_object(obj):
    """ Display an object in a user friendly manner """
    print(obj)
    for section in obj.sections:
        print(section)
    for symbol in obj.symbols:
        print(symbol)
    for reloc in obj.relocations:
        print(reloc)
    for image in obj.images:
        print(image)


def serialize(x):
    """ Serialize an object so it can be json-ified, or serialized """
    res = {}
    if isinstance(x, ObjectFile):
        res["sections"] = []
        for section in x.sections:
            res["sections"].append(serialize(section))

        res["symbols"] = []
        for symbol in x.symbols:
            res["symbols"].append(serialize(symbol))

        res["relocations"] = []
        for reloc in x.relocations:
            res["relocations"].append(serialize(reloc))

        res["images"] = []
        for image in x.images:
            res["images"].append(serialize(image))

        if x.debug_info:
            res["debug"] = debuginfo.serialize(x.debug_info)

        res["arch"] = x.arch.make_id_str()

        if x.entry_symbol_id is not None:
            res["entry_symbol_id"] = x.entry_symbol_id
    elif isinstance(x, Image):
        res["name"] = x.name
        res["address"] = hex(x.address)
        res["sections"] = []
        for section in x.sections:
            res["sections"].append(section.name)
    elif isinstance(x, Section):
        res["name"] = x.name
        res["address"] = hex(x.address)
        res["data"] = bin2asc(x.data)
        res["alignment"] = hex(x.alignment)
    elif isinstance(x, Symbol):
        res["id"] = int(x.id)
        res["name"] = x.name
        res["binding"] = x.binding
        if not x.undefined:
            res["value"] = hex(x.value)
            res["section"] = x.section
        res["typ"] = x.typ
        res["size"] = x.size
    elif isinstance(x, RelocationEntry):
        res["symbol_id"] = x.symbol_id
        res["type"] = x.reloc_type
        res["section"] = x.section
        res["offset"] = hex(x.offset)
        res["addend"] = hex(x.addend)
    else:  # pragma: no cover
        raise NotImplementedError(str(type(x)))
    return res


def deserialize(data):
    """ Create an object file from dict-like data """
    from ..api import get_arch

    arch = get_arch(data["arch"])
    obj = ObjectFile(arch)

    if "entry_symbol_id" in data:
        obj.entry_symbol_id = data["entry_symbol_id"]

    for section in data["sections"]:
        section_object = Section(section["name"])
        obj.add_section(section_object)
        section_object.address = make_num(section["address"])
        section_object.data = asc2bin(section["data"])
        section_object.alignment = make_num(section["alignment"])

    for reloc in data["relocations"]:
        relocation = RelocationEntry(
            reloc["type"],
            int(reloc["symbol_id"]),
            reloc["section"],
            make_num(reloc["offset"]),
            make_num(reloc["addend"]),
        )
        obj.add_relocation(relocation)

    for sym in data["symbols"]:
        # Check for defined / undefined symbol:
        if "value" in sym:
            symbol_value = make_num(sym["value"])
            symbol_section = sym["section"]
        else:
            symbol_value = None
            symbol_section = None

        obj.add_symbol(
            int(sym["id"]),
            sym["name"],
            sym["binding"],
            symbol_value,
            symbol_section,
            sym["typ"],
            sym["size"],
        )

    for image in data["images"]:
        img = Image(image["name"], make_num(image["address"]))
        obj.add_image(img)
        for section_name in image["sections"]:
            assert obj.has_section(section_name)
            img.add_section(obj.get_section(section_name))

    if "debug" in data:
        obj.debug_info = debuginfo.deserialize(data["debug"])
    return obj
