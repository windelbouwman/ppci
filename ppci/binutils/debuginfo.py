
"""
    This module contains classes for storage of debug information.
"""

from ..common import SourceLocation

# TODO: refactor this mess of classes


class DebugInfoIntern:
    """ This presents intermediate form used in the compiler.
        This is a class that can track the location.
        This object is some sort of an internal database.
    """
    def __init__(self):
        self.mappings = {}
        self.infos = []

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
            # print(dst, i)


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
        elif isinstance(di, FuncDebugInfo):
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
        # print('var', name, typ)
        self.variables.append(variable)


class DebugBaseInfo:
    def __init__(self):
        self.section = ''
        self.offset = 0


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


class FuncDebugInfo(DebugBaseInfo):
    """ Info about a function """
    def __init__(self, name, loc):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        self.name = name
        self.loc = loc
        self.begin = 0
        self.end = 0

    def __repr__(self):
        return 'DBGFNC[ {} {} ]'.format(self.name, self.loc)


class DebugLocation(DebugBaseInfo):
    """ Location information """
    def __init__(self, loc):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        # TODO: think of other namings
        self.loc = loc

    def __repr__(self):
        return 'DBGLOC[ {} ]'.format(self.loc)


class DebugVariable(DebugBaseInfo):
    def __init__(self, name, typ, loc):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        assert isinstance(typ, DebugType), str(typ)
        self.name = name
        self.typ = typ
        self.loc = loc
        self.scope = 'global'
        self.loc2 = ''

    def __repr__(self):
        return 'DBGVARRR[ {} {} ]'.format(self.name, self.typ.name)


def write_source_location(loc):
    """ Serialize a location object """
    return {
        'filename': loc.filename,
        'row': loc.row, 'column': loc.col,
        'length': loc.length,
    }


def read_source_location(x):
    loc = SourceLocation(x['filename'], x['row'], x['column'], x['length'])
    return loc


def serialize(x):
    """ Serialize debug information """
    if isinstance(x, DebugLocation):
        x2 = {
            'source': write_source_location(x.loc)
        }
        x2['section'] = x.section
        x2['offset'] = x.offset
        return x2
    elif isinstance(x, FuncDebugInfo):
        return {
            'source': write_source_location(x.loc),
            'function_name': x.name,
            'section': x.section,
            'offset': x.offset,
            'begin': x.begin,
            'end': x.end
        }
    elif isinstance(x, DebugVariable):
        x2 = {
            'source': write_source_location(x.loc),
            'name': x.name,
            'type': x.typ.name,
            'scope': x.scope,
            'location': x.loc2,
        }
        x2['section'] = x.section
        x2['offset'] = x.offset
        return x2
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
        locations = list(map(serialize, x.locations))
        functions = list(map(serialize, x.functions))
        types = list(map(serialize, x.types))
        variables = list(map(serialize, x.variables))
        return {
            'locations': locations,
            'functions': functions,
            'types': types,
            'variables': variables,
        }
    else:
        raise NotImplementedError(str(type(x)))


def deserialize(x):
    """ create debug information from a dict-like object """
    debug_info = DebugInfo()
    for l in x['locations']:
        loc = read_source_location(l['source'])
        dl = DebugLocation(loc)
        dl.section = l['section']
        dl.offset = l['offset']
        debug_info.add(dl)
    for f in x['functions']:
        loc = read_source_location(f['source'])
        fdi = FuncDebugInfo(f['function_name'], loc)
        fdi.section = f['section']
        fdi.offset = f['offset']
        fdi.begin = f['begin']
        fdi.end = f['end']
        debug_info.add(fdi)
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
        loc = read_source_location(v['source'])
        typ = debug_info.get_type(v['type'])
        dv = DebugVariable(v['name'], typ, loc)
        dv.section = v['section']
        dv.offset = v['offset']
        dv.scope = v['scope']
        dv.loc2 = v['location']
        debug_info.add(dv)
    return debug_info
