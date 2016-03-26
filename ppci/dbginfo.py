
"""
    This module contains classes for storage of debug information.
"""

from .common import SourceLocation

# TODO: refactor this mess of classes


class DebugInfo:
    """ Container for debug information. Debug info can be stored here
        in the form of mappings from intermediate code to source locations
        as well as from assembly code to source locations.
    """
    def __init__(self):
        self.mappings = {}

    def map_line(self):
        pass

    def map(self, src, dst):
        """
            Create a projection from src to dst. This means that dst is a
            result of src. So all info attached to src should also be
            attached to dst.
        """
        if src in self.mappings:
            i = self.mappings[src]
            self.mappings[dst] = i
            # print(dst, i)


class BaseInfo:
    pass


class LineInfo:
    pass


class DebugType:
    pass


class CuInfo:
    pass


class FuncDebugInfo(BaseInfo):
    """ Info about a function """
    def __init__(self, name, loc):
        assert isinstance(loc, SourceLocation)
        self.name = name
        self.loc = loc

    def __repr__(self):
        return 'DBGFNC[ {} {} ]'.format(self.name, self.loc)


class DbgLoc(BaseInfo):
    """ Location information """
    def __init__(self, loc):
        assert isinstance(loc, SourceLocation)
        # TODO: think of other namings
        self.loc = loc

    def __repr__(self):
        return 'DBGLOC[ {} ]'.format(self.loc)


def serialize(x):
    if isinstance(x, DbgLoc):
        return {
            'type': 1,
            'filename': x.loc.filename,
            'row': x.loc.row,
            'col': x.loc.col,
            'length': x.loc.length,
        }
    elif isinstance(x, FuncDebugInfo):
        return {
            'type': 2,
            'filename': x.loc.filename,
            'row': x.loc.row,
            'col': x.loc.col,
            'length': x.loc.length,
            'function_name': x.name,
        }
    else:
        raise NotImplementedError(str(type(x)))


def deserialize(x):
    typ = x['type']
    if typ == 1:
        loc = SourceLocation(
            x['filename'],
            x['row'],
            x['col'],
            x['length'])
        return DbgLoc(loc)
    elif typ == 2:
        loc = SourceLocation(
            x['filename'],
            x['row'],
            x['col'],
            x['length'])
        return FuncDebugInfo(x['function_name'], loc)
    else:
        raise NotImplementedError(str(typ))
