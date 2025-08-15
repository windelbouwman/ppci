"""A table with WASM opcodes."""

import enum


class ArgType(enum.Enum):
    TYPE = 1
    HEAPTYPE = 2
    U8 = 3
    U32 = 4
    I32 = 10
    I64 = 11
    F32 = 12
    F64 = 13
    U8x16 = 14
    TYPEIDX = 20
    TABLEIDX = 21
    LOCALIDX = 22
    BLOCKIDX = 23
    FUNCIDX = 24
    LABELIDX = 25
    GLOBALIDX = 26
    ELEMIDX = 27
    DATAIDX = 28


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
    ("ref.null", 0xD0, (ArgType.HEAPTYPE,)),
    ("ref.is_null", 0xD1),
    ("ref.func", 0xD2, (ArgType.FUNCIDX,)),
    ("drop", 0x1A),
    ("select", 0x1B),
    ("select", 0x1C, ("result_types",)),
    ("local.get", 0x20, (ArgType.LOCALIDX,)),
    ("local.set", 0x21, (ArgType.LOCALIDX,)),
    ("local.tee", 0x22, (ArgType.LOCALIDX,)),
    ("global.get", 0x23, (ArgType.GLOBALIDX,)),
    ("global.set", 0x24, (ArgType.GLOBALIDX,)),
    ("table.get", 0x25, (ArgType.TABLEIDX,)),
    ("table.set", 0x26, (ArgType.TABLEIDX,)),
    (
        "table.init",
        (0xFC, 12),
        (ArgType.TABLEIDX, ArgType.ELEMIDX),
        ("i32", "i32", "i32"),
        (),
    ),
    ("elem.drop", (0xFC, 13), (ArgType.ELEMIDX,), (), ()),
    (
        "table.copy",
        (0xFC, 14),
        (ArgType.TABLEIDX, ArgType.TABLEIDX),
        ("i32", "i32", "i32"),
        (),
    ),
    (
        "table.grow",
        (0xFC, 15),
        (ArgType.TABLEIDX,),
        ("funcref", "i32"),
        ("i32",),
    ),
    ("table.size", (0xFC, 16), (ArgType.TABLEIDX,), (), ("i32",)),
    (
        "table.fill",
        (0xFC, 17),
        (ArgType.TABLEIDX,),
        ("i32", "funcref", "i32"),
        (),
    ),
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
    ("memory.size", 0x3F, (ArgType.U8,), (), ("i32",)),
    ("memory.grow", 0x40, (ArgType.U8,), ("i32",), ("i32",)),
    (
        "memory.init",
        (0xFC, 8),
        (ArgType.DATAIDX, ArgType.U8),
        ("i32", "i32", "i32"),
        (),
    ),
    ("data.drop", (0xFC, 9), (ArgType.DATAIDX,)),
    (
        "memory.copy",
        (0xFC, 10),
        (ArgType.U8, ArgType.U8),
        ("i32", "i32", "i32"),
        (),
    ),
    (
        "memory.fill",
        (0xFC, 11),
        (ArgType.U8,),
        ("i32", "i32", "i32"),
        (),
    ),
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
    ("i32.trunc_sat_f32_s", (0xFC, 0), (), ("f32",), ("i32",)),
    ("i32.trunc_sat_f32_u", (0xFC, 1), (), ("f32",), ("i32",)),
    ("i32.trunc_sat_f64_s", (0xFC, 2), (), ("f64",), ("i32",)),
    ("i32.trunc_sat_f64_u", (0xFC, 3), (), ("f64",), ("i32",)),
    ("i64.trunc_sat_f32_s", (0xFC, 4), (), ("f32",), ("i64",)),
    ("i64.trunc_sat_f32_u", (0xFC, 5), (), ("f32",), ("i64",)),
    ("i64.trunc_sat_f64_s", (0xFC, 6), (), ("f64",), ("i64",)),
    ("i64.trunc_sat_f64_u", (0xFC, 7), (), ("f64",), ("i64",)),
    # Vector instructions:
    ("v128.load", (0xFD, 0x0), (ArgType.U32, ArgType.U32)),
    ("v128.load8x8_s", (0xFD, 1), (ArgType.U32, ArgType.U32)),
    ("v128.load8x8_u", (0xFD, 2), (ArgType.U32, ArgType.U32)),
    ("v128.load16x4_s", (0xFD, 3), (ArgType.U32, ArgType.U32)),
    ("v128.load16x4_u", (0xFD, 4), (ArgType.U32, ArgType.U32)),
    ("v128.load32x2_s", (0xFD, 5), (ArgType.U32, ArgType.U32)),
    ("v128.load32x2_u", (0xFD, 6), (ArgType.U32, ArgType.U32)),
    ("v128.load8_splat", (0xFD, 7), (ArgType.U32, ArgType.U32)),
    ("v128.load16_splat", (0xFD, 8), (ArgType.U32, ArgType.U32)),
    ("v128.load32_splat", (0xFD, 9), (ArgType.U32, ArgType.U32)),
    ("v128.load64_splat", (0xFD, 10), (ArgType.U32, ArgType.U32)),
    ("v128.load32_zero", (0xFD, 92), (ArgType.U32, ArgType.U32)),
    ("v128.load64_zero", (0xFD, 93), (ArgType.U32, ArgType.U32)),
    ("v128.store", (0xFD, 11), (ArgType.U32, ArgType.U32)),
    ("v128.load8_lane", (0xFD, 84), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.load16_lane", (0xFD, 85), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.load32_lane", (0xFD, 86), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.load64_lane", (0xFD, 87), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.store8_lane", (0xFD, 88), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.store16_lane", (0xFD, 89), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.store32_lane", (0xFD, 90), (ArgType.U32, ArgType.U32, ArgType.U8)),
    ("v128.store64_lane", (0xFD, 91), (ArgType.U32, ArgType.U32, ArgType.U8)),
    # const
    ("v128.const", (0xFD, 12), (ArgType.U8x16,)),
    ("i8x16.shuffle", (0xFD, 13), (ArgType.U8,) * 16),
    ("i8x16.extract_lane_s", (0xFD, 21), (ArgType.U8,)),
    ("i8x16.extract_lane_u", (0xFD, 22), (ArgType.U8,)),
    ("i8x16.replace_lane", (0xFD, 23), (ArgType.U8,)),
    ("i16x8.extract_lane_s", (0xFD, 24), (ArgType.U8,)),
    ("i16x8.extract_lane_u", (0xFD, 25), (ArgType.U8,)),
    ("i16x8.replace_lane", (0xFD, 26), (ArgType.U8,)),
    ("i32x4.extract_lane", (0xFD, 27), (ArgType.U8,)),
    ("i32x4.replace_lane", (0xFD, 28), (ArgType.U8,)),
    ("i64x2.extract_lane", (0xFD, 29), (ArgType.U8,)),
    ("i64x2.replace_lane", (0xFD, 30), (ArgType.U8,)),
    ("f32x4.extract_lane", (0xFD, 31), (ArgType.U8,)),
    ("f32x4.replace_lane", (0xFD, 32), (ArgType.U8,)),
    ("f64x2.extract_lane", (0xFD, 33), (ArgType.U8,)),
    ("f64x2.replace_lane", (0xFD, 34), (ArgType.U8,)),
    # swizzle / splat:
    ("i8x16.swizzle", (0xFD, 14)),
    ("i8x16.splat", (0xFD, 15)),
    ("i16x8.splat", (0xFD, 16)),
    ("i32x4.splat", (0xFD, 17)),
    ("i64x2.splat", (0xFD, 18)),
    ("f32x4.splat", (0xFD, 19)),
    ("f64x2.splat", (0xFD, 20)),
    # i8x16:
    ("i8x16.eq", (0xFD, 35)),
    ("i8x16.ne", (0xFD, 36)),
    ("i8x16.lt_s", (0xFD, 37)),
    ("i8x16.lt_u", (0xFD, 38)),
    ("i8x16.gt_s", (0xFD, 39)),
    ("i8x16.gt_u", (0xFD, 40)),
    ("i8x16.le_s", (0xFD, 41)),
    ("i8x16.le_u", (0xFD, 42)),
    ("i8x16.ge_s", (0xFD, 43)),
    ("i8x16.ge_u", (0xFD, 44)),
    # i16x8:
    ("i16x8.eq", (0xFD, 45)),
    ("i16x8.ne", (0xFD, 46)),
    ("i16x8.lt_s", (0xFD, 47)),
    ("i16x8.lt_u", (0xFD, 48)),
    ("i16x8.gt_s", (0xFD, 49)),
    ("i16x8.gt_u", (0xFD, 50)),
    ("i16x8.le_s", (0xFD, 51)),
    ("i16x8.le_u", (0xFD, 52)),
    ("i16x8.ge_s", (0xFD, 53)),
    ("i16x8.ge_u", (0xFD, 54)),
    # i32x4:
    ("i32x4.eq", (0xFD, 55)),
    ("i32x4.ne", (0xFD, 56)),
    ("i32x4.lt_s", (0xFD, 57)),
    ("i32x4.lt_u", (0xFD, 58)),
    ("i32x4.gt_s", (0xFD, 59)),
    ("i32x4.gt_u", (0xFD, 60)),
    ("i32x4.le_s", (0xFD, 61)),
    ("i32x4.le_u", (0xFD, 62)),
    ("i32x4.ge_s", (0xFD, 63)),
    ("i32x4.ge_u", (0xFD, 64)),
    # i64x2:
    ("i64x2.eq", (0xFD, 214)),
    ("i64x2.ne", (0xFD, 215)),
    ("i64x2.lt_s", (0xFD, 216)),
    ("i64x2.gt_s", (0xFD, 217)),
    ("i64x2.le_s", (0xFD, 218)),
    ("i64x2.ge_s", (0xFD, 219)),
    # f32x4
    ("f32x4.eq", (0xFD, 65)),
    ("f32x4.ne", (0xFD, 66)),
    ("f32x4.lt", (0xFD, 67)),
    ("f32x4.gt", (0xFD, 68)),
    ("f32x4.le", (0xFD, 69)),
    ("f32x4.ge", (0xFD, 70)),
    # f64x2:
    ("f64x2.eq", (0xFD, 71)),
    ("f64x2.ne", (0xFD, 72)),
    ("f64x2.lt", (0xFD, 73)),
    ("f64x2.gt", (0xFD, 74)),
    ("f64x2.le", (0xFD, 75)),
    ("f64x2.ge", (0xFD, 76)),
    # v128:
    ("v128.not", (0xFD, 77)),
    ("v128.and", (0xFD, 78)),
    ("v128.andnot", (0xFD, 79)),
    ("v128.or", (0xFD, 80)),
    ("v128.xor", (0xFD, 81)),
    ("v128.bitselect", (0xFD, 82)),
    ("v128.any_true", (0xFD, 83)),
    # i8x16:
    ("i8x16.abs", (0xFD, 96)),
    ("i8x16.neg", (0xFD, 97)),
    ("i8x16.popcnt", (0xFD, 98)),
    ("i8x16.all_true", (0xFD, 99)),
    ("i8x16.bitmask", (0xFD, 100)),
    ("i8x16.narrow_i16x8_s", (0xFD, 101)),
    ("i8x16.narrow_i16x8_u", (0xFD, 102)),
    ("i8x16.shl", (0xFD, 107)),
    ("i8x16.shr_s", (0xFD, 108)),
    ("i8x16.shr_u", (0xFD, 109)),
    ("i8x16.add", (0xFD, 110)),
    ("i8x16.add_sat_s", (0xFD, 111)),
    ("i8x16.add_sat_u", (0xFD, 112)),
    ("i8x16.sub", (0xFD, 113)),
    ("i8x16.sub_sat_s", (0xFD, 114)),
    ("i8x16.sub_sat_u", (0xFD, 115)),
    ("i8x16.min_s", (0xFD, 118)),
    ("i8x16.min_u", (0xFD, 119)),
    ("i8x16.max_s", (0xFD, 120)),
    ("i8x16.max_u", (0xFD, 121)),
    ("i8x16.avgr_u", (0xFD, 123)),
    # i16x8:
    ("i16x8.extadd_pairwise_i8x16_s", (0xFD, 124)),
    ("i16x8.extadd_pairwise_i8x16_u", (0xFD, 125)),
    ("i16x8.abs", (0xFD, 128)),
    ("i16x8.neg", (0xFD, 129)),
    ("i16x8.q15mulr_sat_s", (0xFD, 130)),
    ("i16x8.all_true", (0xFD, 131)),
    ("i16x8.bitmask", (0xFD, 132)),
    ("i16x8.narrow_i32x4_s", (0xFD, 133)),
    ("i16x8.narrow_i32x4_u", (0xFD, 134)),
    ("i16x8.extend_low_i8x16_s", (0xFD, 135)),
    ("i16x8.extend_high_i8x16_s", (0xFD, 136)),
    ("i16x8.extend_low_i8x16_u", (0xFD, 137)),
    ("i16x8.extend_high_i8x16_u", (0xFD, 138)),
    ("i16x8.shl", (0xFD, 139)),
    ("i16x8.shr_s", (0xFD, 140)),
    ("i16x8.shr_u", (0xFD, 141)),
    ("i16x8.add", (0xFD, 142)),
    ("i16x8.add_sat_s", (0xFD, 143)),
    ("i16x8.add_sat_u", (0xFD, 144)),
    ("i16x8.sub", (0xFD, 145)),
    ("i16x8.sub_sat_s", (0xFD, 146)),
    ("i16x8.sub_sat_u", (0xFD, 147)),
    ("i16x8.mul", (0xFD, 149)),
    ("i16x8.min_s", (0xFD, 150)),
    ("i16x8.min_u", (0xFD, 151)),
    ("i16x8.max_s", (0xFD, 152)),
    ("i16x8.max_u", (0xFD, 153)),
    ("i16x8.avgr_u", (0xFD, 155)),
    ("i16x8.extmul_low_i8x16_s", (0xFD, 156)),
    ("i16x8.extmul_high_i8x16_s", (0xFD, 157)),
    ("i16x8.extmul_low_i8x16_u", (0xFD, 158)),
    ("i16x8.extmul_high_i8x16_u", (0xFD, 159)),
    # i32x4:
    ("i32x4.extadd_pairwise_i16x8_s", (0xFD, 126)),
    ("i32x4.extadd_pairwise_i16x8_u", (0xFD, 127)),
    ("i32x4.abs", (0xFD, 160)),
    ("i32x4.neg", (0xFD, 161)),
    ("i32x4.all_true", (0xFD, 163)),
    ("i32x4.bitmask", (0xFD, 164)),
    ("i32x4.extend_low_i16x8_s", (0xFD, 167)),
    ("i32x4.extend_high_i16x8_s", (0xFD, 168)),
    ("i32x4.extend_low_i16x8_u", (0xFD, 169)),
    ("i32x4.extend_high_i16x8_u", (0xFD, 170)),
    ("i32x4.shl", (0xFD, 171)),
    ("i32x4.shr_s", (0xFD, 172)),
    ("i32x4.shr_u", (0xFD, 173)),
    ("i32x4.add", (0xFD, 174)),
    ("i32x4.sub", (0xFD, 177)),
    ("i32x4.mul", (0xFD, 181)),
    ("i32x4.min_s", (0xFD, 182)),
    ("i32x4.min_u", (0xFD, 183)),
    ("i32x4.max_s", (0xFD, 184)),
    ("i32x4.max_u", (0xFD, 185)),
    ("i32x4.dot_i16x8_s", (0xFD, 186)),
    ("i32x4.extmul_low_i16x8_s", (0xFD, 188)),
    ("i32x4.extmul_high_i16x8_s", (0xFD, 189)),
    ("i32x4.extmul_low_i16x8_u", (0xFD, 190)),
    ("i32x4.extmul_high_i16x8_u", (0xFD, 191)),
    # i64x2:
    ("i64x2.abs", (0xFD, 192)),
    ("i64x2.neg", (0xFD, 193)),
    ("i64x2.all_true", (0xFD, 195)),
    ("i64x2.bitmask", (0xFD, 196)),
    ("i64x2.extend_low_i32x4_s", (0xFD, 199)),
    ("i64x2.extend_high_i32x4_s", (0xFD, 200)),
    ("i64x2.extend_low_i32x4_u", (0xFD, 201)),
    ("i64x2.extend_high_i32x4_u", (0xFD, 202)),
    ("i64x2.shl", (0xFD, 203)),
    ("i64x2.shr_s", (0xFD, 204)),
    ("i64x2.shr_u", (0xFD, 205)),
    ("i64x2.add", (0xFD, 206)),
    ("i64x2.sub", (0xFD, 209)),
    ("i64x2.mul", (0xFD, 213)),
    ("i64x2.extmul_low_i32x4_s", (0xFD, 220)),
    ("i64x2.extmul_high_i32x4_s", (0xFD, 221)),
    ("i64x2.extmul_low_i32x4_u", (0xFD, 222)),
    ("i64x2.extmul_high_i32x4_u", (0xFD, 223)),
    # f32x4:
    ("f32x4.ceil", (0xFD, 103)),
    ("f32x4.floor", (0xFD, 104)),
    ("f32x4.trunc", (0xFD, 105)),
    ("f32x4.nearest", (0xFD, 106)),
    ("f32x4.abs", (0xFD, 224)),
    ("f32x4.neg", (0xFD, 225)),
    ("f32x4.sqrt", (0xFD, 227)),
    ("f32x4.add", (0xFD, 228)),
    ("f32x4.sub", (0xFD, 229)),
    ("f32x4.mul", (0xFD, 230)),
    ("f32x4.div", (0xFD, 231)),
    ("f32x4.min", (0xFD, 232)),
    ("f32x4.max", (0xFD, 233)),
    ("f32x4.pmin", (0xFD, 234)),
    ("f32x4.pmax", (0xFD, 235)),
    # f64x2:
    ("f64x2.ceil", (0xFD, 116)),
    ("f64x2.floor", (0xFD, 117)),
    ("f64x2.trunc", (0xFD, 122)),
    ("f64x2.nearest", (0xFD, 148)),
    ("f64x2.abs", (0xFD, 236)),
    ("f64x2.neg", (0xFD, 237)),
    ("f64x2.sqrt", (0xFD, 239)),
    ("f64x2.add", (0xFD, 240)),
    ("f64x2.sub", (0xFD, 241)),
    ("f64x2.mul", (0xFD, 242)),
    ("f64x2.div", (0xFD, 243)),
    ("f64x2.min", (0xFD, 244)),
    ("f64x2.max", (0xFD, 245)),
    ("f64x2.pmin", (0xFD, 246)),
    ("f64x2.pmax", (0xFD, 247)),
    # Conversions:
    ("i32x4.trunc_sat_f32x4_s", (0xFD, 248)),
    ("i32x4.trunc_sat_f32x4_u", (0xFD, 249)),
    ("f32x4.convert_i32x4_s", (0xFD, 250)),
    ("f32x4.convert_i32x4_u", (0xFD, 251)),
    ("i32x4.trunc_sat_f64x2_s_zero", (0xFD, 252)),
    ("i32x4.trunc_sat_f64x2_u_zero", (0xFD, 253)),
    ("f64x2.convert_low_i32x4_s", (0xFD, 254)),
    ("f64x2.convert_low_i32x4_u", (0xFD, 255)),
    ("f32x4.demote_f64x2_zero", (0xFD, 94)),
    ("f64x2.promote_low_f32x4", (0xFD, 95)),
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


I = _make_instructionset()  # noqa


def eval_expr(expr):
    """Evaluate a sequence of instructions"""
    stack = []
    for i in expr:
        consumed_types, produced_types, action = EVAL[i.opcode]
        if action is None:
            raise RuntimeError(f"Cannot evaluate {i.opcode}")
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
