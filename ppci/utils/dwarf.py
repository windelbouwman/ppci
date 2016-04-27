"""
    Implementation of the dwarf debugging format.

    See also: http://dwarfstd.org/
"""

# TODO: implement

TAG_ARRAY_TYPE = 0x1
TAG_POINTER_TYPE = 0xf
TAG_COMPILE_UNIT = 0x11
TAG_BASE_TYPE = 0x24
TAG_VARIABLE = 0x34


class CompileUnit:
    pass


class SubProgram:
    def __init__(self):
        self.name = None


class Variable:
    pass


class DwarfReader:
    pass


class DwarfWriter:
    pass
