
"""
    This module contains classes for storage of debug information.
"""

from ..common import SourceLocation


class DebugDb:
    """ This presents intermediate form used in the compiler.
        This is a class that can track the location.
        This object is some sort of an internal database.
    """
    def __init__(self):
        self.mappings = {}
        self.infos = []
        self.label_nr = 0

    def new_label(self):
        """ Create a new label name that is unique """
        self.label_nr += 1
        return '.LDBG_{}'.format(self.label_nr)

    def enter(self, a, di):
        """ Register debug info as a result of something """
        self.mappings[a] = di
        self.add(di)

    def contains(self, src):
        return src in self.mappings

    def add(self, di):
        assert di not in self.infos
        self.infos.append(di)

    def get(self, src):
        return self.mappings[src]

    def map(self, src, dst):
        """
            Create a projection from src to dst. This means that dst is a
            result of src. So all info attached to src should also be
            attached to dst.
        """
        if src in self.mappings:
            info = self.mappings[src]
            self.mappings[dst] = info
            # print(dst, info)


class DebugInfo:
    """ Container for debug information. Debug info can be stored here
        in the form of mappings from intermediate code to source locations
        as well as from assembly code to source locations.
    """
    def __init__(self):
        self.locations = []
        self.functions = []
        self.types = []
        self.types_map = {}
        self.variables = []

    def all_items(self):
        for l in self.locations:
            yield l
        for l in self.functions:
            yield l
        for l in self.types:
            yield l
        for l in self.variables:
            yield l

    def add(self, di):
        if isinstance(di, DebugLocation):
            self.add_location(di)
        elif isinstance(di, DebugType):
            self.add_type(di)
        elif isinstance(di, DebugVariable):
            self.add_variable(di)
        elif isinstance(di, DebugFunction):
            self.functions.append(di)
        else:
            raise NotImplementedError(str(di))

    def add_location(self, l):
        self.locations.append(l)

    def add_type(self, typ):
        """ Register a type """
        # print(typ)
        if typ.name not in self.types_map:
            self.types_map[typ.name] = typ
            self.types.append(typ)
        else:
            pass
            # TODO: assert equal?

    def get_type(self, name):
        """ Get a type with a given name """
        return self.types_map[name]

    def has_type(self, name):
        return name in self.types_map

    def add_variable(self, variable):
        self.variables.append(variable)


class DebugBaseInfo:
    def __init__(self):
        pass


class LineInfo:
    pass


class CuInfo:
    pass


class DebugType:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'DBGTYP[ {} {} ]'.format(self.name, type(self))


class DebugBaseType(DebugType):
    def __init__(self, name, size, encoding):
        super().__init__(name)
        self.size = size
        self.encoding = encoding

    def __repr__(self):
        return self.name


class DebugStructType(DebugType):
    """ A structured type """
    def __init__(self, name):
        super().__init__(name)
        self.fields = []

    def add_field(self, name, typ, offset):
        assert isinstance(typ, DebugType)
        self.fields.append((name, typ, offset))

    def __repr__(self):
        return 'struct'


class DebugPointerType(DebugType):
    """ A type that points somewhere else """
    def __init__(self, name, pointed_type):
        super().__init__(name)
        assert isinstance(pointed_type, DebugType)
        self.pointed_type = pointed_type

    def __repr__(self):
        return '*{}'.format(self.pointed_type)


class DebugArrayType(DebugType):
    def __init__(self, name, element_type, size):
        super().__init__(name)
        assert isinstance(element_type, DebugType)
        assert isinstance(size, int)
        self.element_type = element_type
        self.size = size

    def __repr__(self):
        return '{}[{}]'.format(self.element_type, self.size)


class DebugFormalParameter:
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ


class DebugFunction(DebugBaseInfo):
    """ Info about a function """
    def __init__(self, name, loc, begin=0, end=0, variables=()):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        self.name = name
        self.loc = loc
        self.begin = begin
        self.end = end
        self.variables = list(variables)

    def __repr__(self):
        return 'DBGFNC[ {} {} begin={}, end={} ]'.format(
            self.name, self.loc, self.begin, self.end)

    def add_variable(self, variable):
        self.variables.append(variable)


class DebugAddress:
    def __init__(self, section, offset):
        self.section = section
        self.offset = offset


class DebugLocation(DebugBaseInfo):
    """ Location information """
    def __init__(self, loc, address=None):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        self.loc = loc
        self.address = address

    def __repr__(self):
        return 'DBGLOC[ {} addr={} ]'.format(self.loc, self.address)


class DebugVariable(DebugBaseInfo):
    def __init__(self, name, typ, loc, scope='global', address=None):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        assert isinstance(typ, DebugType), str(typ)
        self.name = name
        self.typ = typ
        self.loc = loc
        self.scope = scope
        self.address = address

    def __repr__(self):
        return 'DBGVARRR[ {} {} {} ]'.format(
            self.name, self.typ.name, self.address)


def write_source_location(loc):
    """ Serialize a location object """
    return {
        'filename': loc.filename, 'row': loc.row, 'column': loc.col,
        'length': loc.length,
    }


def read_source_location(x):
    loc = SourceLocation(x['filename'], x['row'], x['column'], x['length'])
    return loc


def write_address(address):
    assert isinstance(address, DebugAddress)
    return {'section': address.section, 'offset': address.offset}


def read_address(x):
    return DebugAddress(x['section'], x['offset'])


def serialize(x):
    """ Serialize debug information """
    if isinstance(x, DebugLocation):
        return {
            'source': write_source_location(x.loc),
            'address': write_address(x.address),
        }
    elif isinstance(x, DebugFunction):
        variables = []
        for v in x.variables:
            variables.append({
                'source': write_source_location(v.loc),
                'name': v.name,
                'type': v.typ.name,
            })
        return {
            'source': write_source_location(x.loc),
            'function_name': x.name,
            'begin': write_address(x.begin),
            'end': write_address(x.end),
            'variables': variables,
        }
    elif isinstance(x, DebugVariable):
        return {
            'source': write_source_location(x.loc),
            'name': x.name,
            'type': x.typ.name,
            'scope': x.scope,
            'address': write_address(x.address),
        }
    elif isinstance(x, DebugBaseType):
        return {
            'kind': 'base',
            'name': x.name,
            'size': x.size,
        }
    elif isinstance(x, DebugStructType):
        fields = []
        for field in x.fields:
            fields.append({
                'name': field[0],
                'typ': field[1].name,
                'offset': field[2],
                })
        return {
            'kind': 'struct',
            'name': x.name,
            'fields': fields,
        }
    elif isinstance(x, DebugArrayType):
        return {
            'kind': 'array',
            'name': x.name,
            'element_type': x.element_type.name,
            'size': x.size,
        }
    elif isinstance(x, DebugPointerType):
        return {
            'kind': 'pointer',
            'name': x.name,
            'pointed_type': x.pointed_type.name,
        }
    elif isinstance(x, DebugInfo):
        locations = [serialize(l) for l in x.locations]
        types = list(map(serialize, x.types))
        variables = list(map(serialize, x.variables))
        functions = list(map(serialize, x.functions))
        return {
            'locations': locations,
            'types': types,
            'variables': variables,
            'functions': functions,
        }
    else:
        raise NotImplementedError(str(type(x)))


def deserialize(x):
    """ create debug information from a dict-like object """
    debug_info = DebugInfo()
    for l in x['locations']:
        loc = read_source_location(l['source'])
        address = read_address(l['address'])
        dl = DebugLocation(loc, address=address)
        debug_info.add(dl)
    for t in x['types']:
        kind = t['kind']
        name = t['name']
        if kind == 'base':
            size = t['size']
            dt = DebugBaseType(name, size, 1)
        elif kind == 'struct':
            dt = DebugStructType(name)
        elif kind == 'pointer':
            ptype = debug_info.get_type(t['pointed_type'])
            dt = DebugPointerType(name, ptype)
        elif kind == 'array':
            etype = debug_info.get_type(t['element_type'])
            dt = DebugArrayType(name, etype, t['size'])
        else:
            raise NotImplementedError(kind)
        debug_info.add(dt)
    for v in x['variables']:
        name = v['name']
        loc = read_source_location(v['source'])
        typ = debug_info.get_type(v['type'])
        address = read_address(v['address'])
        dv = DebugVariable(name, typ, loc, scope=v['scope'], address=address)
        debug_info.add(dv)
    for f in x['functions']:
        loc = read_source_location(f['source'])
        begin = read_address(f['begin'])
        end = read_address(f['end'])
        variables = []
        for v in f['variables']:
            name = v['name']
            loc = read_source_location(v['source'])
            typ = debug_info.get_type(v['type'])
            dv = DebugVariable(name, typ, loc)
            variables.append(dv)
        fdi = DebugFunction(
            f['function_name'], loc, begin=begin, end=end, variables=variables)
        debug_info.add(fdi)
    return debug_info
