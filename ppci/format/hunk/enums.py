""" Hunk file constants.

Some constants as can be found here:

https://en.wikipedia.org/wiki/Amiga_Hunk
"""

HUNK_UNIT = 0x3E7
HUNK_NAME = 0x3E8
HUNK_CODE = 0x3E9
HUNK_DATA = 0x3EA
HUNK_BSS = 0x3EB
HUNK_RELOC32 = 0x3EC
HUNK_RELOC16 = 0x3ED
HUNK_RELOC8 = 0x3EE

HUNK_SYMBOL = 0x3F0
HUNK_DEBUG = 0x3F1
HUNK_END = 0x3F2
HUNK_HEADER = 0x3F3

HUNK_DREL32 = 0x3F7
HUNK_DREL16 = 0x3F8
HUNK_DREL8 = 0x3F9
HUNK_LIB = 0x3FA
HUNK_INDEX = 0x3FB
HUNK_RELOC32SHORT = 0x3FC
HUNK_RELRELOC32 = 0x3FD
HUNK_ABSRELOC16 = 0x3FE

names = {
    HUNK_UNIT: "Unit",
    HUNK_NAME: "Name",
    HUNK_CODE: "Code",
    HUNK_DATA: "Data",
    HUNK_BSS: "Bss",
    HUNK_RELOC32: "Reloc32",
    HUNK_RELOC16: "Reloc16",
    HUNK_RELOC8: "Reloc8",
    HUNK_SYMBOL: "Symbol",
    HUNK_DEBUG: "Debug",
    HUNK_END: "End",
    HUNK_HEADER: "Header",
}


def get_name(code):
    if code in names:
        return names[code]
    else:
        return "<unknown>"
