
"""
    This module contains classes for storage of debug information.
"""

import logging
from collections import namedtuple
from ..common import SourceLocation


class DebugDb:
    """ This presents intermediate form used in the compiler.
        This is a class that can track the location.
        This object is some sort of an internal database.
    """
    logger = logging.getLogger('debugdb')

    def __init__(self):
        self.mappings = {}
        self.infos = []
        self.label_nr = 0

    def new_label(self):
        """ Create a new label name that is unique """
        self.label_nr += 1
        return '.LDBG_{}'.format(self.label_nr)

    def enter(self, src, info):
        """ Register debug info as a result of something """
        self.mappings[src] = info
        self.add(info)
        self.logger.debug('Add "%s" <- "%s"', info, src)

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
            # assert dst not in self.mappings
            self.mappings[dst] = info
            self.logger.debug('Map "%s" <- "%s" to "%s"', info, src, dst)


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
            self.add_function(di)
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

    def add_function(self, function):
        self.functions.append(function)


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


# TODO: change name to FixedAddress?
class DebugAddress:
    """ A single point into the code at some place """
    def __init__(self, section, offset):
        self.section = section
        self.offset = offset


class FpOffsetAddress:
    def __init__(self, offset):
        self.offset = offset

    def __repr__(self):
        return '@(FP + {})'.format(self.offset)


class UnknownAddress:
    pass


class TemporalDebugAddress:
    """ A location depending on the position of the instruction ptr """
    def __init__(self, start, end, address):
        self.begin = start
        self.end = end
        self.address = address


class DebugLocation(DebugBaseInfo):
    """ Location information """
    def __init__(self, loc: SourceLocation, address=None):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        self.loc = loc
        self.address = address

    def __repr__(self):
        return 'DBGLOC[ {} addr={} ]'.format(self.loc, self.address)


class DebugVariable(DebugBaseInfo):
    def __init__(
            self, name, typ: DebugType, loc: SourceLocation, address=None):
        super().__init__()
        assert isinstance(loc, SourceLocation)
        assert isinstance(typ, DebugType), str(typ)
        self.name = name
        self.typ = typ
        self.loc = loc
        if address is None:
            address = UnknownAddress()
        self.address = address

    def __repr__(self):
        return 'DBGVAR[ {} {} {} ]'.format(
            self.name, self.typ, self.address)


def serialize(debug_info):
    """ Serialize debug information into a dict """
    return DictSerializer().serialize(debug_info)


class DebugInfoReplicator:
    """ Create a copy of debug info and all referred stuff """
    def replicate(self, debug_info_in, debug_info_out):
        """ Replicate debug info from one object into the other """
        for location in debug_info_in.locations:
            debug_info_out.add(self.do_location(location))
        for function in debug_info_in.functions:
            debug_info_out.add(self.do_function(function))
        for typ in debug_info_in.types:
            debug_info_out.add(self.do_type(typ))
        for variable in debug_info_in.variables:
            debug_info_out.add(self.do_variable(variable))

    def do_location(self, location):
        """ Process location information """
        address = self.do_address(location.address)
        return DebugLocation(location.loc, address=address)

    def do_function(self, function):
        """ Replicate function debug information """
        begin = self.do_address(function.begin)
        end = self.do_address(function.end)
        variables = [self.do_variable(v) for v in function.variables]
        return DebugFunction(
            function.name, function.loc,
            begin=begin, end=end, variables=variables)

    def do_type(self, typ):
        # TODO: create copies of typ class?
        return typ

    def do_variable(self, variable):
        """ Replicate a variable """
        address = self.do_address(variable.address)
        return DebugVariable(
            variable.name, variable.typ, variable.loc, address=address)

    def do_address(self, address):
        """ Replicate an address """
        if isinstance(address, DebugAddress):
            return DebugAddress(address.section, address.offset)
        elif isinstance(address, FpOffsetAddress):
            return FpOffsetAddress(address.offset)
        elif isinstance(address, UnknownAddress):
            return UnknownAddress()
        else:  # pragma: no cover
            raise NotImplementedError(str(address))


class SectionAdjustingReplicator(DebugInfoReplicator):
    """ Replicate debug information, but shift offsets in sections by
        the amount given in the offsets dictionary """
    def __init__(self, offsets):
        self.offsets = offsets

    def do_address(self, address):
        if isinstance(address, DebugAddress):
            offset = address.offset + self.offsets[address.section]
            return DebugAddress(address.section, offset)
        else:
            return super().do_address(address)


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
        """ Create dict for a location """
        return {
            'source': self.write_source_location(loc.loc),
            'address': self.write_address(loc.address),
        }

    def serialize_function(self, function):
        """ Turn a function into a dict """
        variables = [self.serialize_variable(v) for v in function.variables]
        return {
            'source': self.write_source_location(function.loc),
            'function_name': function.name,
            'begin': self.write_address(function.begin),
            'end': self.write_address(function.end),
            'variables': variables,
        }

    def serialize_variable(self, var):
        """ Turn a variable into a dictionary """
        address = self.write_address(var.address)
        return {
            'source': self.write_source_location(var.loc),
            'name': var.name,
            'type': self.get_type_id(var.typ),
            'address': address,
        }

    def serialize_type(self, typ):
        """ Serialize a type to dictionary """
        i = self.get_type_id(typ)
        if isinstance(typ, DebugBaseType):
            return {
                'id': i,
                'kind': 'base',
                'name': typ.name,
                'size': typ.size,
            }
        elif isinstance(typ, DebugStructType):
            fields = []
            for field in typ.fields:
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
        elif isinstance(typ, DebugArrayType):
            return {
                'id': i,
                'kind': 'array',
                'element_type': self.get_type_id(typ.element_type),
                'size': typ.size,
            }
        elif isinstance(typ, DebugPointerType):
            return {
                'id': i,
                'kind': 'pointer',
                'pointed_type': self.get_type_id(typ.pointed_type),
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(type(typ)))

    def write_source_location(self, loc):
        """ Serialize a location object """
        return {
            'filename': loc.filename,
            'row': loc.row,
            'column': loc.col,
            'length': loc.length,
        }

    def write_address(self, address):
        """ Generate an address into a dict """
        if isinstance(address, DebugAddress):
            return {
                'kind': 'fixed',
                'section': address.section,
                'offset': address.offset
            }
        elif isinstance(address, FpOffsetAddress):
            return {
                'kind': 'fprel',
                'offset': address.offset
            }
        elif isinstance(address, UnknownAddress):
            return {
                'kind': 'unknown'
            }
        else:  # pragma: no cover
            raise NotImplementedError(str(address))

    def get_type_id(self, typ):
        """ Get or create a unique id for the given type """
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
            debug_info.add(self.read_variable(v))
        for f in x['functions']:
            loc = self.read_source_location(f['source'])
            begin = self.read_address(f['begin'])
            end = self.read_address(f['end'])
            variables = []
            for v in f['variables']:
                variables.append(self.read_variable(v))
            fdi = DebugFunction(
                f['function_name'], loc, begin=begin, end=end,
                variables=variables)
            debug_info.add(fdi)
        return debug_info

    def read_variable(self, v):
        name = v['name']
        loc = self.read_source_location(v['source'])
        typ = self.get_type(v['type'])
        address = self.read_address(v['address'])
        return DebugVariable(name, typ, loc, address=address)

    def read_source_location(self, x):
        return SourceLocation(
            x['filename'], x['row'], x['column'], x['length'])

    def read_address(self, x):
        kind = x['kind']
        if kind == 'fixed':
            return DebugAddress(x['section'], x['offset'])
        elif kind == 'fprel':
            return FpOffsetAddress(x['offset'])
        elif kind == 'unknown':
            return UnknownAddress()
        else:  # pragma: no cover
            raise NotImplementedError(kind)

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
        else:  # pragma: no cover
            raise NotImplementedError(kind)
        return self.types[idx]
