""" A table with WASM opcodes. """

# Note: left out 32bit opcodes at first. Added them later, but I might have
# missed some.

# Gargantual table with all instructions in it.
# From this table different dictionaries are created. One for encoding
# and another for decoding wasm.
# Columns: mnemonic, opcode, operands, stack inputs, stack outputs,
#  action function
instruction_table = [
    ('unreachable', 0x00, (), (), ()),
    ('nop', 0x01),
    ('block', 0x02, ('type',)),
    ('loop', 0x03, ('type',)),
    ('if', 0x04, ('type',)),
    ('else', 0x05),
    ('end', 0x0b, (), (), (), lambda i, v: ()),
    ('br', 0x0c, ('u32',)),
    ('br_if', 0x0d, ('u32',)),
    ('br_table', 0x0e, ('br_table',)),
    ('return', 0x0f),

    ('call', 0x10, ('u32',)),
    ('call_indirect', 0x11, ('u32', 'u32')),

    ('drop', 0x1a),
    ('select', 0x1b),

    ('get_local', 0x20, ('u32',)),
    ('set_local', 0x21, ('u32',)),
    ('tee_local', 0x22, ('u32',)),
    ('get_global', 0x23, ('u32',)),
    ('set_global', 0x24, ('u32',)),

    ('i32.load', 0x28, ('u32', 'u32')),
    ('i64.load', 0x29, ('u32', 'u32')),
    ('f32.load', 0x2a, ('u32', 'u32')),
    ('f64.load', 0x2b, ('u32', 'u32')),
    ('i32.load8_s', 0x2c, ('u32', 'u32')),
    ('i32.load8_u', 0x2d, ('u32', 'u32')),
    ('i32.load16_s', 0x2e, ('u32', 'u32')),
    ('i32.load16_u', 0x2f, ('u32', 'u32')),
    ('i64.load8_s', 0x30, ('u32', 'u32')),
    ('i64.load8_u', 0x31, ('u32', 'u32')),
    ('i64.load16_s', 0x32, ('u32', 'u32')),
    ('i64.load16_u', 0x33, ('u32', 'u32')),
    ('i64.load32_s', 0x34, ('u32', 'u32')),
    ('i64.load32_u', 0x35, ('u32', 'u32')),

    ('i32.store8', 0x3a, ('u32', 'u32')),
    ('i32.store16', 0x3b, ('u32', 'u32')),
    ('i32.store', 0x36, ('u32', 'u32')),
    ('i64.store', 0x37, ('u32', 'u32')),
    ('f32.store', 0x38, ('u32', 'u32')),
    ('f64.store', 0x39, ('u32', 'u32')),
    ('current_memory', 0x3f, ('byte',)),
    ('grow_memory', 0x40, ('byte',)),

    ('i32.const', 0x41, ('i32',), (), ('i32',), lambda i, v: (i.args[0],)),
    ('i64.const', 0x42, ('i64',), (), ('i64',)),
    ('f32.const', 0x43, ('f32',), (), ('f32',)),
    ('f64.const', 0x44, ('f64',), (), ('f64',)),

    ('i32.eqz', 0x45),
    ('i32.eq', 0x46),
    ('i32.ne', 0x47),
    ('i32.lt_s', 0x48),
    ('i32.lt_u', 0x49),
    ('i32.gt_s', 0x4a),
    ('i32.gt_u', 0x4b),
    ('i32.le_s', 0x4c),
    ('i32.le_u', 0x4d),
    ('i32.ge_s', 0x4e),
    ('i32.ge_u', 0x4f),
    ('i64.eqz', 0x50),
    ('i64.eq', 0x51),
    ('i64.ne', 0x52),
    ('i64.lt_s', 0x53),
    ('i64.lt_u', 0x54),
    ('i64.gt_s', 0x55),
    ('i64.gt_u', 0x56),
    ('i64.le_s', 0x57),
    ('i64.le_u', 0x58),
    ('i64.ge_s', 0x59),
    ('i64.ge_u', 0x5a),
    ('f32.eq', 0x5b),
    ('f32.ne', 0x5c),
    ('f32.lt', 0x5d),
    ('f32.gt', 0x5e),
    ('f32.le', 0x5f),
    ('f32.ge', 0x60),
    ('f64.eq', 0x61),
    ('f64.ne', 0x62),
    ('f64.lt', 0x63),
    ('f64.gt', 0x64),
    ('f64.le', 0x65),
    ('f64.ge', 0x66),

    ('i32.clz', 0x67),
    ('i32.ctz', 0x68),
    ('i32.popcnt', 0x69),
    ('i32.add', 0x6a),
    ('i32.sub', 0x6b),
    ('i32.mul', 0x6c),
    ('i32.div_s', 0x6d),
    ('i32.div_u', 0x6e),
    ('i32.rem_s', 0x6f),
    ('i32.rem_u', 0x70),
    ('i32.and', 0x71),
    ('i32.or', 0x72),
    ('i32.xor', 0x73),
    ('i32.shl', 0x74),
    ('i32.shr_s', 0x75),
    ('i32.shr_u', 0x76),
    ('i32.rotl', 0x77),
    ('i32.rotr', 0x78),
    ('i64.clz', 0x79),
    ('i64.ctz', 0x7a),
    ('i64.popcnt', 0x7b),
    ('i64.add', 0x7c),
    ('i64.sub', 0x7d),
    ('i64.mul', 0x7e),
    ('i64.div_s', 0x7f),
    ('i64.div_u', 0x80),
    ('i64.rem_s', 0x81),
    ('i64.rem_u', 0x82),
    ('i64.and', 0x83),
    ('i64.or', 0x84),
    ('i64.xor', 0x85),
    ('i64.shl', 0x86),
    ('i64.shr_s', 0x87),
    ('i64.shr_u', 0x88),
    ('i64.rotl', 0x89),
    ('i64.rotr', 0x8a),
    ('f32.abs', 0x8b),
    ('f32.neg', 0x8c),
    ('f32.ceil', 0x8d),
    ('f32.floor', 0x8e),
    ('f32.trunc', 0x8f),
    ('f32.nearest', 0x90),
    ('f32.sqrt', 0x91),
    ('f32.add', 0x92),
    ('f32.sub', 0x93),
    ('f32.mul', 0x94),
    ('f32.div', 0x95),
    ('f32.min', 0x96),
    ('f32.max', 0x97),
    ('f32.copysign', 0x98),
    ('f64.abs', 0x99),
    ('f64.neg', 0x9a),
    ('f64.ceil', 0x9b),
    ('f64.floor', 0x9c),
    ('f64.trunc', 0x9d),
    ('f64.nearest', 0x9e),
    ('f64.sqrt', 0x9f),
    ('f64.add', 0xa0),
    ('f64.sub', 0xa1),
    ('f64.mul', 0xa2),
    ('f64.div', 0xa3),
    ('f64.min', 0xa4),
    ('f64.max', 0xa5),
    ('f64.copysign', 0xa6),

    ('i32.wrap/i64', 0xa7),
    ('i32.trunc_s/f32', 0xa8),
    ('i32.trunc_u/f32', 0xa9),
    ('i32.trunc_s/f64', 0xaa),
    ('i32.trunc_u/f64', 0xab),
    ('i64.extend_s/i32', 0xac),
    ('i64.extend_u/i32', 0xad),
    ('i64.trunc_s/f32', 0xae),
    ('i64.trunc_u/f32', 0xaf),
    ('i64.trunc_s/f64', 0xb0),
    ('i64.trunc_u/f64', 0xb1),
    ('f32.convert_s/i32', 0xb2),
    ('f32.convert_u/i32', 0xb3),
    ('f32.convert_s/i64', 0xb4),
    ('f32.convert_u/i64', 0xb5),
    ('f32.demote/f64', 0xb6),
    ('f64.convert_s/i32', 0xb7),
    ('f64.convert_u/i32', 0xb8),
    ('f64.convert_s/i64', 0xb9),
    ('f64.convert_u/i64', 0xba),
    ('f64.promote/f32', 0xbb),

    ('i32.reinterpret/f32', 0xbc),
    ('i64.reinterpret/f64', 0xbd),
    ('f32.reinterpret/i32', 0xbe),
    ('f64.reinterpret/i64', 0xbf),

]

OPCODES = {r[0]: r[1] for r in instruction_table}
REVERZ = {r[1]: r[0] for r in instruction_table}

OPERANDS = {r[0]: r[2] if len(r) > 2 else () for r in instruction_table}
EVAL = {
    r[0]: (r[3], r[4], r[5])
    if len(r) >= 6 else ((), (), None) for r in instruction_table}

STORE_OPS = {
    'f64.store',
    'f32.store',
    'i64.store',
    'i64.store8',
    'i64.store16',
    'i64.store32',
    'i32.store',
    'i32.store8',
    'i32.store16',
}

LOAD_OPS = {
    'f64.load',
    'f32.load',
    'i64.load',
    'i64.load8_u',
    'i64.load8_s',
    'i64.load16_u',
    'i64.load16_s',
    'i64.load32_u',
    'i64.load32_s',
    'i32.load',
    'i32.load8_u',
    'i32.load8_s',
    'i32.load16_u',
    'i32.load16_s',
}

# Generate an instructionset object that supports autocompletion


class Instructionset:
    pass


def _make_instructionset():
    main_i = Instructionset()

    for opcode in OPCODES:
        opcode = opcode.replace('/', '_')
        parts = opcode.split('.')
        i = main_i
        for part in parts[:-1]:
            if not hasattr(i, part):
                setattr(i, part, Instructionset())
            i = getattr(i, part)
        setattr(i, parts[-1], opcode)
    return main_i


I = _make_instructionset()
