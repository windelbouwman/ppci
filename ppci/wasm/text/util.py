import io


def default_alignment(opcode):
    """ Retrieve the default alignment for a memory opcode.

    Note that the alignment is returned as log2

    For example:
    i64.load16_u -> default align = 1
    i32.load8_s -> default align = 0
    i32.store -> default align = 2
    """
    ty, opcode2 = opcode.split(".")
    if opcode2 in {"load", "store"}:
        align = _ty_alignments[ty]
    else:
        align = _opcode2_alignments[opcode2]
    return align


_ty_alignments = {
    "i32": 2,
    "i64": 3,
    "f32": 2,
    "f64": 3,
}


_opcode2_alignments = {
    "load8_u": 0,
    "load8_s": 0,
    "load16_u": 1,
    "load16_s": 1,
    "load32_u": 2,
    "load32_s": 2,
    "store8": 0,
    "store16": 1,
    "store32": 2,
}


def log2(value):
    return _log2[value]


_log2 = {
    1: 0,
    2: 1,
    4: 2,
    8: 3,
    16: 4,
    32: 5,
    64: 6,
    128: 7,
    256: 8,
}


def bytes2datastring(b):
    """
    Allow most ascii characters, except for

    double quote (34)
    backslash (92)

    """
    f = io.StringIO()
    for v in b:
        if 32 <= v < 127 and v not in (34, 92):
            f.write(chr(v))
        else:
            f.write("\\" + hex(v)[2:].rjust(2, "0"))
    return f.getvalue()
