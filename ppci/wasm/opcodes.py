""" A table with WASM opcodes. """

import enum


class ArgType(enum.Enum):
    TYPE = 1
    BYTE = 2
    U32 = 3
    I32 = 10
    I64 = 11
    F32 = 12
    F64 = 13
    TYPEIDX = 20
    TABLEIDX = 21
    LOCALIDX = 22
    BLOCKIDX = 23
    FUNCIDX = 24
    LABELIDX = 25
    GLOBALIDX = 26


class Space(enum.Enum):
    TYPE = 0
    TABLE = 1
    LOCAL = 2
    BLOCK = 3
    FUNC = 4
    LABEL = 5


# Note: left out 32bit opcodes at first. Added them later, but I might have
# missed some.

# Gargantual table with all instructions in it.
# From this table different dictionaries are created. One for encoding
# and another for decoding wasm.
# Columns: mnemonic, opcode, operands, stack inputs, stack outputs,
#  action function
instruction_table = [
    ("unreachable", 0x00, (), (), ()),
    ("nop", 0x01),
    ("block", 0x02, (ArgType.TYPE,)),
    ("loop", 0x03, (ArgType.TYPE,)),
    ("if", 0x04, (ArgType.TYPE,)),
    ("else", 0x05),
    ("end", 0x0B, (), (), (), lambda i, v: ()),
    ("br", 0x0C, (ArgType.LABELIDX,)),
    ("br_if", 0x0D, (ArgType.LABELIDX,)),
    ("br_table", 0x0E, ("br_table",)),
    ("return", 0x0F),
    ("call", 0x10, (ArgType.FUNCIDX,)),  # funcidx
    (
        "call_indirect",
        0x11,
        (ArgType.TYPEIDX, ArgType.TABLEIDX),
    ),  # typeidx, tableidx
    ("drop", 0x1A),
    ("select", 0x1B),
    ("local.get", 0x20, (ArgType.LOCALIDX,)),
    ("local.set", 0x21, (ArgType.LOCALIDX,)),
    ("local.tee", 0x22, (ArgType.LOCALIDX,)),
    ("global.get", 0x23, (ArgType.GLOBALIDX,)),
    ("global.set", 0x24, (ArgType.GLOBALIDX,)),
    ("i32.load", 0x28, (ArgType.U32, ArgType.U32)),
    ("i64.load", 0x29, (ArgType.U32, ArgType.U32)),
    ("f32.load", 0x2A, (ArgType.U32, ArgType.U32)),
    ("f64.load", 0x2B, (ArgType.U32, ArgType.U32)),
    ("i32.load8_s", 0x2C, (ArgType.U32, ArgType.U32)),
    ("i32.load8_u", 0x2D, (ArgType.U32, ArgType.U32)),
    ("i32.load16_s", 0x2E, (ArgType.U32, ArgType.U32)),
    ("i32.load16_u", 0x2F, (ArgType.U32, ArgType.U32)),
    ("i64.load8_s", 0x30, (ArgType.U32, ArgType.U32)),
    ("i64.load8_u", 0x31, (ArgType.U32, ArgType.U32)),
    ("i64.load16_s", 0x32, (ArgType.U32, ArgType.U32)),
    ("i64.load16_u", 0x33, (ArgType.U32, ArgType.U32)),
    ("i64.load32_s", 0x34, (ArgType.U32, ArgType.U32)),
    ("i64.load32_u", 0x35, (ArgType.U32, ArgType.U32)),
    ("i32.store", 0x36, (ArgType.U32, ArgType.U32)),
    ("i64.store", 0x37, (ArgType.U32, ArgType.U32)),
    ("f32.store", 0x38, (ArgType.U32, ArgType.U32)),
    ("f64.store", 0x39, (ArgType.U32, ArgType.U32)),
    ("i32.store8", 0x3A, (ArgType.U32, ArgType.U32)),
    ("i32.store16", 0x3B, (ArgType.U32, ArgType.U32)),
    ("i64.store8", 0x3C, (ArgType.U32, ArgType.U32)),
    ("i64.store16", 0x3D, (ArgType.U32, ArgType.U32)),
    ("i64.store32", 0x3E, (ArgType.U32, ArgType.U32)),
    ("memory.size", 0x3F, ("byte",), (), ("i32",)),
    ("memory.grow", 0x40, ("byte",), ("i32",), ("i32",)),
    (
        "i32.const",
        0x41,
        (ArgType.I32,),
        (),
        ("i32",),
        lambda i, v: (i.args[0],),
    ),
    (
        "i64.const",
        0x42,
        (ArgType.I64,),
        (),
        ("i64",),
        lambda i, v: (i.args[0],),
    ),
    (
        "f32.const",
        0x43,
        (ArgType.F32,),
        (),
        ("f32",),
        lambda i, v: (i.args[0],),
    ),
    (
        "f64.const",
        0x44,
        (ArgType.F64,),
        (),
        ("f64",),
        lambda i, v: (i.args[0],),
    ),
    ("i32.eqz", 0x45),
    ("i32.eq", 0x46),
    ("i32.ne", 0x47),
    ("i32.lt_s", 0x48),
    ("i32.lt_u", 0x49),
    ("i32.gt_s", 0x4A),
    ("i32.gt_u", 0x4B),
    ("i32.le_s", 0x4C),
    ("i32.le_u", 0x4D),
    ("i32.ge_s", 0x4E),
    ("i32.ge_u", 0x4F),
    ("i64.eqz", 0x50),
    ("i64.eq", 0x51),
    ("i64.ne", 0x52),
    ("i64.lt_s", 0x53),
    ("i64.lt_u", 0x54),
    ("i64.gt_s", 0x55),
    ("i64.gt_u", 0x56),
    ("i64.le_s", 0x57),
    ("i64.le_u", 0x58),
    ("i64.ge_s", 0x59),
    ("i64.ge_u", 0x5A),
    ("f32.eq", 0x5B),
    ("f32.ne", 0x5C),
    ("f32.lt", 0x5D),
    ("f32.gt", 0x5E),
    ("f32.le", 0x5F),
    ("f32.ge", 0x60),
    ("f64.eq", 0x61),
    ("f64.ne", 0x62),
    ("f64.lt", 0x63),
    ("f64.gt", 0x64),
    ("f64.le", 0x65),
    ("f64.ge", 0x66),
    ("i32.clz", 0x67, (), ("i32",), ("i32",)),
    ("i32.ctz", 0x68, (), ("i32",), ("i32",)),
    ("i32.popcnt", 0x69, (), ("i32",), ("i32",)),
    ("i32.add", 0x6A, (), ("i32", "i32"), ("i32",)),
    ("i32.sub", 0x6B, (), ("i32", "i32"), ("i32",)),
    ("i32.mul", 0x6C, (), ("i32", "i32"), ("i32",)),
    ("i32.div_s", 0x6D, (), ("i32", "i32"), ("i32",)),
    ("i32.div_u", 0x6E, (), ("i32", "i32"), ("i32",)),
    ("i32.rem_s", 0x6F, (), ("i32", "i32"), ("i32",)),
    ("i32.rem_u", 0x70, (), ("i32", "i32"), ("i32",)),
    ("i32.and", 0x71, (), ("i32", "i32"), ("i32",)),
    ("i32.or", 0x72, (), ("i32", "i32"), ("i32",)),
    ("i32.xor", 0x73, (), ("i32", "i32"), ("i32",)),
    ("i32.shl", 0x74, (), ("i32", "i32"), ("i32",)),
    ("i32.shr_s", 0x75, (), ("i32", "i32"), ("i32",)),
    ("i32.shr_u", 0x76, (), ("i32", "i32"), ("i32",)),
    ("i32.rotl", 0x77, (), ("i32", "i32"), ("i32",)),
    ("i32.rotr", 0x78, (), ("i32", "i32"), ("i32",)),
    ("i64.clz", 0x79, (), ("i64",), ("i64",)),
    ("i64.ctz", 0x7A, (), ("i64",), ("i64",)),
    ("i64.popcnt", 0x7B, (), ("i64",), ("i64",)),
    ("i64.add", 0x7C, (), ("i64", "i64"), ("i64",)),
    ("i64.sub", 0x7D, (), ("i64", "i64"), ("i64",)),
    ("i64.mul", 0x7E, (), ("i64", "i64"), ("i64",)),
    ("i64.div_s", 0x7F, (), ("i64", "i64"), ("i64",)),
    ("i64.div_u", 0x80, (), ("i64", "i64"), ("i64",)),
    ("i64.rem_s", 0x81, (), ("i64", "i64"), ("i64",)),
    ("i64.rem_u", 0x82, (), ("i64", "i64"), ("i64",)),
    ("i64.and", 0x83, (), ("i64", "i64"), ("i64",)),
    ("i64.or", 0x84, (), ("i64", "i64"), ("i64",)),
    ("i64.xor", 0x85, (), ("i64", "i64"), ("i64",)),
    ("i64.shl", 0x86, (), ("i64", "i64"), ("i64",)),
    ("i64.shr_s", 0x87, (), ("i64", "i64"), ("i64",)),
    ("i64.shr_u", 0x88, (), ("i64", "i64"), ("i64",)),
    ("i64.rotl", 0x89, (), ("i64", "i64"), ("i64",)),
    ("i64.rotr", 0x8A, (), ("i64", "i64"), ("i64",)),
    ("f32.abs", 0x8B, (), ("f32",), ("f32",)),
    ("f32.neg", 0x8C, (), ("f32",), ("f32",)),
    ("f32.ceil", 0x8D, (), ("f32",), ("f32",)),
    ("f32.floor", 0x8E, (), ("f32",), ("f32",)),
    ("f32.trunc", 0x8F, (), ("f32",), ("f32",)),
    ("f32.nearest", 0x90, (), ("f32",), ("f32",)),
    ("f32.sqrt", 0x91, (), ("f32",), ("f32",)),
    ("f32.add", 0x92, (), ("f32", "f32"), ("f32",)),
    ("f32.sub", 0x93, (), ("f32", "f32"), ("f32",)),
    ("f32.mul", 0x94, (), ("f32", "f32"), ("f32",)),
    ("f32.div", 0x95, (), ("f32", "f32"), ("f32",)),
    ("f32.min", 0x96, (), ("f32", "f32"), ("f32",)),
    ("f32.max", 0x97, (), ("f32", "f32"), ("f32",)),
    ("f32.copysign", 0x98, (), ("f32", "f32"), ("f32",)),
    ("f64.abs", 0x99, (), ("f64",), ("f64",)),
    ("f64.neg", 0x9A, (), ("f64",), ("f64",)),
    ("f64.ceil", 0x9B, (), ("f64",), ("f64",)),
    ("f64.floor", 0x9C, (), ("f64",), ("f64",)),
    ("f64.trunc", 0x9D, (), ("f64",), ("f64",)),
    ("f64.nearest", 0x9E, (), ("f64",), ("f64",)),
    ("f64.sqrt", 0x9F, (), ("f64",), ("f64",)),
    ("f64.add", 0xA0, (), ("f64", "f64"), ("f64",)),
    ("f64.sub", 0xA1, (), ("f64", "f64"), ("f64",)),
    ("f64.mul", 0xA2, (), ("f64", "f64"), ("f64",)),
    ("f64.div", 0xA3, (), ("f64", "f64"), ("f64",)),
    ("f64.min", 0xA4, (), ("f64", "f64"), ("f64",)),
    ("f64.max", 0xA5, (), ("f64", "f64"), ("f64",)),
    ("f64.copysign", 0xA6, (), ("f64", "f64"), ("f64",)),
    ("i32.wrap_i64", 0xA7),
    ("i32.trunc_f32_s", 0xA8, (), ("f32",), ("i32",)),
    ("i32.trunc_f32_u", 0xA9, (), ("f32",), ("i32",)),
    ("i32.trunc_f64_s", 0xAA, (), ("f64",), ("i32",)),
    ("i32.trunc_f64_u", 0xAB, (), ("f64",), ("i32",)),
    ("i64.extend_i32_s", 0xAC, (), ("i32",), ("i64",)),
    ("i64.extend_i32_u", 0xAD, (), ("i32",), ("i64",)),
    ("i64.trunc_f32_s", 0xAE, (), ("f32",), ("i64",)),
    ("i64.trunc_f32_u", 0xAF, (), ("f32",), ("i64",)),
    ("i64.trunc_f64_s", 0xB0, (), ("f64",), ("i64",)),
    ("i64.trunc_f64_u", 0xB1, (), ("f64",), ("i64",)),
    ("f32.convert_i32_s", 0xB2, (), ("i32",), ("f32",)),
    ("f32.convert_i32_u", 0xB3, (), ("i32",), ("f32",)),
    ("f32.convert_i64_s", 0xB4, (), ("i64",), ("f32",)),
    ("f32.convert_i64_u", 0xB5, (), ("i64",), ("f32",)),
    ("f32.demote_f64", 0xB6, (), ("f64",), ("f32",)),
    ("f64.convert_i32_s", 0xB7, (), ("i32",), ("f64",)),
    ("f64.convert_i32_u", 0xB8, (), ("i32",), ("f64",)),
    ("f64.convert_i64_s", 0xB9, (), ("i64",), ("f64",)),
    ("f64.convert_i64_u", 0xBA, (), ("i64",), ("f64",)),
    ("f64.promote_f32", 0xBB, (), ("f32",), ("f64",)),
    ("i32.reinterpret_f32", 0xBC, (), ("f32",), ("i32",)),
    ("i64.reinterpret_f64", 0xBD, (), ("f64",), ("i64",)),
    ("f32.reinterpret_i32", 0xBE, (), ("i32",), ("f32",)),
    ("f64.reinterpret_i64", 0xBF, (), ("i64",), ("f64",)),
    ("i32.extend8_s", 0xC0, (), ("i32",), ("i32",)),
    ("i32.extend16_s", 0xC1, (), ("i32",), ("i32",)),
    ("i64.extend8_s", 0xC2, (), ("i64",), ("i64",)),
    ("i64.extend16_s", 0xC3, (), ("i64",), ("i64",)),
    ("i64.extend32_s", 0xC4, (), ("i64",), ("i64",)),
    ("i32.trunc_sat_f32_s", (0xFC, 0x0), (), ("f32",), ("i32",)),
    ("i32.trunc_sat_f32_u", (0xFC, 0x1), (), ("f32",), ("i32",)),
    ("i32.trunc_sat_f64_s", (0xFC, 0x2), (), ("f64",), ("i32",)),
    ("i32.trunc_sat_f64_u", (0xFC, 0x3), (), ("f64",), ("i32",)),
    ("i64.trunc_sat_f32_s", (0xFC, 0x4), (), ("f32",), ("i64",)),
    ("i64.trunc_sat_f32_u", (0xFC, 0x5), (), ("f32",), ("i64",)),
    ("i64.trunc_sat_f64_s", (0xFC, 0x6), (), ("f64",), ("i64",)),
    ("i64.trunc_sat_f64_u", (0xFC, 0x7), (), ("f64",), ("i64",)),
]

OPCODES = {r[0]: r[1] for r in instruction_table}
REVERZ = {r[1]: r[0] for r in instruction_table}

OPERANDS = {r[0]: r[2] if len(r) > 2 else () for r in instruction_table}
EVAL = {
    r[0]: (r[3], r[4], r[5]) if len(r) >= 6 else ((), (), None)
    for r in instruction_table
}

STACK_IO = {
    r[0]: (r[3], r[4]) if len(r) >= 5 else None for r in instruction_table
}

STORE_OPS = {
    "f64.store",
    "f32.store",
    "i64.store",
    "i64.store8",
    "i64.store16",
    "i64.store32",
    "i32.store",
    "i32.store8",
    "i32.store16",
}

LOAD_OPS = {
    "f64.load",
    "f32.load",
    "i64.load",
    "i64.load8_u",
    "i64.load8_s",
    "i64.load16_u",
    "i64.load16_s",
    "i64.load32_u",
    "i64.load32_s",
    "i32.load",
    "i32.load8_u",
    "i32.load8_s",
    "i32.load16_u",
    "i32.load16_s",
}

BINOPS = {
    "f64.add",
    "f64.sub",
    "f64.mul",
    "f64.div",
    "f32.add",
    "f32.sub",
    "f32.mul",
    "f32.div",
    "i64.add",
    "i64.sub",
    "i64.mul",
    "i32.add",
    "i32.sub",
    "i32.mul",
    "i64.div_s",
    "i64.div_u",
    "i32.div_s",
    "i32.div_u",
    "i32.rem_u",
    "i32.rem_s",
    "i64.rem_u",
    "i64.rem_s",
    "i64.and",
    "i64.or",
    "i64.xor",
    "i64.shl",
    "i64.shr_s",
    "i64.shr_u",
    "i32.and",
    "i32.or",
    "i32.xor",
    "i32.shl",
    "i32.shr_s",
    "i32.shr_u",
}

CASTOPS = {
    "i32.wrap_i64",
    "i64.extend_i32_s",
    "i64.extend_i32_u",
    "f64.convert_i32_s",
    "f64.convert_i32_u",
    "f64.convert_i64_s",
    "f64.convert_i64_u",
    "f32.convert_i32_s",
    "f32.convert_i32_u",
    "f32.convert_i64_s",
    "f32.convert_i64_u",
}

CMPOPS = {
    "f64.eq",
    "f64.ne",
    "f64.ge",
    "f64.gt",
    "f64.le",
    "f64.lt",
    "f32.eq",
    "f32.ne",
    "f32.ge",
    "f32.gt",
    "f32.le",
    "f32.lt",
    "i32.eqz",
    "i32.eq",
    "i32.ne",
    "i32.lt_s",
    "i32.lt_u",
    "i32.gt_s",
    "i32.gt_u",
    "i32.le_s",
    "i32.le_u",
    "i32.ge_s",
    "i32.ge_u",
    "i64.eqz",
    "i64.eq",
    "i64.ne",
    "i64.lt_s",
    "i64.lt_u",
    "i64.gt_s",
    "i64.gt_u",
    "i64.le_s",
    "i64.le_u",
    "i64.ge_s",
    "i64.ge_u",
}

# Generate an instructionset object that supports autocompletion


class Instructionset:
    pass


def _make_instructionset():
    main_i = Instructionset()

    for opcode in OPCODES:
        opcode = opcode.replace("/", "_")
        parts = opcode.split(".")
        i = main_i
        for part in parts[:-1]:
            if not hasattr(i, part):
                setattr(i, part, Instructionset())
            i = getattr(i, part)
        setattr(i, parts[-1], opcode)
    return main_i


I = _make_instructionset()


def eval_expr(expr):
    """ Evaluate a sequence of instructions """
    stack = []
    for i in expr:
        consumed_types, produced_types, action = EVAL[i.opcode]
        if action is None:
            raise RuntimeError("Cannot evaluate {}".format(i.opcode))
        # Gather stack values:
        values = []
        for t in consumed_types:
            vt, v = stack.pop(-1)
            assert vt == t
            values.append(v)

        # Perform magic action of instruction:
        values = action(i, values)

        # Push results on tha stack:
        assert len(values) == len(produced_types)
        for vt, v in zip(produced_types, values):
            stack.append((vt, v))

    if len(stack) == 1:
        return stack[0]
    else:
        raise ValueError("Expression does not leave value on stack!")
