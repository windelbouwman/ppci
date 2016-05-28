
"""
    This module contains classes for storage of debug information.
"""

from collections import namedtuple
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
        # TODO: implement a check here? Do this otherways?
        if typ not in self.types:
            self.types.append(typ)

    def add_variable(self, variable):
        self.variables.append(variable)


class DebugBaseInfo:
    def __init__(self):
        pass


class LineInfo:
    pass


class DebugType:
    """ Debug type base class """
    def __init__(self):
        pass

    def __repr__(self):
        return 'DBGTYP[ {} ]'.format(type(self))

    def sizeof(self):
        """ Determine the size of a debug type """
        raise NotImplementedError()


class DebugBaseType(DebugType):
    def __init__(self, name, size, encoding):
        super().__init__()
        self.name = name
        self.size = size
        self.encoding = encoding

    def __repr__(self):
        return self.name

    def sizeof(self):
        """ Determine the size of a debug type """
        return self.size


DebugStructField = namedtuple('DebugStructField', ['name', 'typ', 'offset'])


class DebugStructType(DebugType):
    """ A structured type """
    def __init__(self):
        super().__init__()
        self.fields = []

    def add_field(self, name, typ, offset):
        assert isinstance(typ, DebugType)
        self.fields.append(DebugStructField(name, typ, offset))

    def has_field(self, name):
        return name in (f.name for f in self.fields)

    def get_field(self, name):
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)

    def __repr__(self):
        return 'struct {...}'

    def sizeof(self):
        """ Determine the size of a debug type """
        return sum(field.typ.sizeof() for field in self.fields)


class DebugPointerType(DebugType):
    """ A type that points somewhere else """
    def __init__(self, pointed_type):
        super().__init__()
        assert isinstance(pointed_type, DebugType)
        self.pointed_type = pointed_type

    def __repr__(self):
        return '*{}'.format(self.pointed_type)


class DebugArrayType(DebugType):
    def __init__(self, element_type, size):
        super().__init__()
        assert isinstance(element_type, DebugType)
        assert isinstance(size, int)
        self.element_type = element_type
        self.size = size

    def __repr__(self):
        return '{}[{}]'.format(self.element_type, self.size)

    def sizeof(self):
        """ Determine the size of a debug type """
        return self.size * self.element_type.sizeof()


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
        return 'DBGVAR[ {} {} {} ]'.format(
            self.name, self.typ, self.address)


def serialize(debug_info):
    """ Serialize debug information into a dict """
    return DictSerializer().serialize(debug_info)


class DictSerializer:
    """ Serialize debug information into dictionary format """
    def __init__(self):
        self.type_ids = {}

    def serialize(self, dbi):
        """ Serialize debug information """
        # Clear type id's:
        self.type_ids.clear()

        locations = [self.serialize_location(l) for l in dbi.locations]
        types = list(map(self.serialize_type, dbi.types))
        variables = list(map(self.serialize_variable, dbi.variables))
        functions = list(map(self.serialize_function, dbi.functions))
        return {
            'locations': locations,
            'types': types,
            'variables': variables,
            'functions': functions,
        }

    def serialize_location(self, loc):
        return {
            'source': self.write_source_location(loc.loc),
            'address': self.write_address(loc.address),
        }

    def serialize_function(self, x):
        variables = []
        for v in x.variables:
            variables.append({
                'source': self.write_source_location(v.loc),
                'name': v.name,
                'type': self.get_type_id(v.typ),
            })
        return {
            'source': self.write_source_location(x.loc),
            'function_name': x.name,
            'begin': self.write_address(x.begin),
            'end': self.write_address(x.end),
            'variables': variables,
        }

    def serialize_variable(self, x):
        return {
            'source': self.write_source_location(x.loc),
            'name': x.name,
            'type': self.get_type_id(x.typ),
            'scope': x.scope,
            'address': self.write_address(x.address),
        }

    def serialize_type(self, x):
        i = self.get_type_id(x)
        if isinstance(x, DebugBaseType):
            return {
                'id': i,
                'kind': 'base',
                'name': x.name,
                'size': x.size,
            }
        elif isinstance(x, DebugStructType):
            fields = []
            for field in x.fields:
                fields.append({
                    'name': field.name,
                    'type': self.get_type_id(field.typ),
                    'offset': field.offset,
                    })
            return {
                'id': i,
                'kind': 'struct',
                'fields': fields,
            }
        elif isinstance(x, DebugArrayType):
            return {
                'id': i,
                'kind': 'array',
                'element_type': self.get_type_id(x.element_type),
                'size': x.size,
            }
        elif isinstance(x, DebugPointerType):
            return {
                'id': i,
                'kind': 'pointer',
                'pointed_type': self.get_type_id(x.pointed_type),
            }
        else:
            raise NotImplementedError(str(type(x)))

    def write_source_location(self, loc):
        """ Serialize a location object """
        return {
            'filename': loc.filename,
            'row': loc.row,
            'column': loc.col,
            'length': loc.length,
        }

    def write_address(self, address):
        assert isinstance(address, DebugAddress)
        return {'section': address.section, 'offset': address.offset}

    def get_type_id(self, typ):
        if typ not in self.type_ids:
            self.type_ids[typ] = len(self.type_ids)
        return self.type_ids[typ]


def deserialize(x):
    return DictDeserializer().deserialize(x)


class DictDeserializer:
    """ Deserialize dict data into debug information """
    def __init__(self):
        self.type_ids = {}

    def deserialize(self, x):
        """ create debug information from a dict-like object """
        # Clear map:
        self.types = {}
        self.type_worklist = {}

        # Start reading debug info:
        debug_info = DebugInfo()
        for l in x['locations']:
            loc = self.read_source_location(l['source'])
            address = self.read_address(l['address'])
            dl = DebugLocation(loc, address=address)
            debug_info.add(dl)
        for t in x['types']:
            i = t['id']
            self.type_worklist[i] = t
        # print(self.type_worklist)
        for t in x['types']:
            dt = self.get_type(t['id'])
            debug_info.add(dt)
        for v in x['variables']:
            name = v['name']
            loc = self.read_source_location(v['source'])
            typ = self.get_type(v['type'])
            address = self.read_address(v['address'])
            dv = DebugVariable(
                name, typ, loc, scope=v['scope'], address=address)
            debug_info.add(dv)
        for f in x['functions']:
            loc = self.read_source_location(f['source'])
            begin = self.read_address(f['begin'])
            end = self.read_address(f['end'])
            variables = []
            for v in f['variables']:
                name = v['name']
                loc = self.read_source_location(v['source'])
                typ = self.get_type(v['type'])
                dv = DebugVariable(name, typ, loc)
                variables.append(dv)
            fdi = DebugFunction(
                f['function_name'], loc, begin=begin, end=end,
                variables=variables)
            debug_info.add(fdi)
        return debug_info

    def read_source_location(self, x):
        return SourceLocation(
            x['filename'], x['row'], x['column'], x['length'])

    def read_address(self, x):
        return DebugAddress(x['section'], x['offset'])

    def get_type(self, idx):
        """ Get type from data or from cache """
        if idx in self.types:
            return self.types[idx]

        t = self.type_worklist.pop(idx)
        kind = t['kind']
        if kind == 'base':
            name = t['name']
            size = t['size']
            dt = DebugBaseType(name, size, 1)
            self.types[idx] = dt
        elif kind == 'struct':
            dt = DebugStructType()

            # Store it here, to prevent block error on recursive type:
            self.types[idx] = dt

            # Process fields:
            for field in t['fields']:
                name = field['name']
                offset = field['offset']
                field_typ = self.get_type(field['type'])
                dt.add_field(name, field_typ, offset)
        elif kind == 'pointer':
            ptype = self.get_type(t['pointed_type'])
            dt = DebugPointerType(ptype)
            self.types[idx] = dt
        elif kind == 'array':
            etype = self.get_type(t['element_type'])
            dt = DebugArrayType(etype, t['size'])
            self.types[idx] = dt
        else:
            raise NotImplementedError(kind)
        return self.types[idx]
