""" Hunk file constants.

Some constants as can be found here:

https://en.wikipedia.org/wiki/Amiga_Hunk
"""

HUNK_UNIT = 0x3e7
HUNK_NAME = 0x3e8
HUNK_CODE = 0x3e9
HUNK_DATA = 0x3ea
HUNK_BSS = 0x3eb
HUNK_RELOC32 = 0x3ec
HUNK_RELOC16 = 0x3ed
HUNK_RELOC8 = 0x3ee

HUNK_SYMBOL = 0x3f0
HUNK_DEBUG = 0x3f1
HUNK_END = 0x3f2
HUNK_HEADER = 0x3f3

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
