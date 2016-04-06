
"""
    This module contains classes for storage of debug information.
"""

from ..common import SourceLocation

# TODO: refactor this mess of classes


class DebugInfoIntern:
    """ This presents intermediate form used in the compiler.
        This is a class that can track the location.
    """
    def __init__(self):
        self.mappings = {}
        self.infos = []

    def enter(self, a, di):
        """ Register debug info as a result of something """
        self.mappings[a] = di
        self.add(di)

    def add(self, di):
        assert di not in self.infos
        self.infos.append(di)

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
            self.types.append(di)
        elif isinstance(di, DebugVariable):
            self.variables.append(di)
        elif isinstance(di, FuncDebugInfo):
            self.functions.append(di)
        else:
            raise NotImplementedError(str(di))

    def add_location(self, l):
        self.locations.append(l)

    def add_type(self, typ):
        """ Register a type """
        # print(typ)
        if typ.name not in self.types:
            self.types[typ.name] = typ
        return self.types[typ.name]

    def add_variable(self, name, typ, loc):
        # print('var', name, typ)
        dbg_var = DebugVariable(name, typ, loc)
        self.vars[dbg_var.name] = dbg_var
        return dbg_var

    def add_parameter(self, name, typ, loc):
        # print('parameter', name, typ)
        dbg_var = DebugFormalParameter(name, typ)
        self.vars[dbg_var.name] = dbg_var
        return dbg_var


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


class DebugBaseType(DebugType):
    def __init__(self, name, byte_size, encoding):
        super().__init__(name)
        self.byte_size = byte_size
        self.encoding = encoding


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
        self.name = name
        assert isinstance(typ, str), str(typ)
        self.typ = typ
        self.loc = loc


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
        x2 = {
            'source': write_source_location(x.loc)
        }
        x2['function_name'] = x.name
        x2['section'] = x.section
        x2['offset'] = x.offset
        return x2
    elif isinstance(x, DebugVariable):
        scope = 'global'
        x2 = {
            'source': write_source_location(x.loc),
            'var_name': x.name,
            'var_type': x.typ,
            'var_scope': scope,
        }
        x2['section'] = x.section
        x2['offset'] = x.offset
        return x2
    elif isinstance(x, DebugBaseType):
        return {
            'typ_name': x.name,
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
        debug_info.add(fdi)
    for t in x['types']:
        dt = DebugBaseType(t['typ_name'], 4, 1)
        debug_info.add(dt)
    for v in x['variables']:
        loc = read_source_location(v['source'])
        dv = DebugVariable(v['var_name'], v['var_type'], loc)
        dv.section = v['section']
        dv.offset = v['offset']
        debug_info.add(dv)
    return debug_info
