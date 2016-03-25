
"""
    This module contains classes for storage of debug information.
"""


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


class LineInfo:
    pass


class DebugType:
    pass


class CuInfo:
    pass


class FuncInfo:
    pass


class DbgLoc:
    def __init__(self, a):
        # TODO: think of other namings
        self.a = a

    def __repr__(self):
        return 'DBGLOC[ {} ]'.format(self.a)
