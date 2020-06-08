""" Generate random wasm programs.

Idea: generate random wasm programs and test
if they compile and have the same result.

Run this with:

    $ python -m pytest -v -s wasm.py

Or just as a script:

    $ python wasm.py

"""

from hypothesis import given, assume, settings, strategies as st
from hypothesis.strategies import integers, composite
from ppci.wasm import Module, instantiate

# Create wasm module strategy?
# Function strategy?

# Instruction strategies:
i64_const = st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: ('i64.const', x))

i64_load_opcode = st.sampled_from([
    'i64.load',
    'i64.load32_s',
    'i64.load32_u',
    'i64.load16_s',
    'i64.load16_u',
    'i64.load8_s',
    'i64.load8_u',
])


@composite
def i64_load(draw):
    opcode = draw(i64_load_opcode)
    base = draw(st.integers(min_value=0, max_value=9))
    offset = draw(st.integers(min_value=0, max_value=11))
    return (opcode, 'offset={}'.format(offset), ('i32.const', base))


@composite
def i64_store(draw):
    opcode = draw(i64_store_opcodes)
    value = draw(i64_value)
    base = draw(st.integers(min_value=0, max_value=9))
    offset = draw(st.integers(min_value=0, max_value=11))
    return (
        opcode, 'offset={}'.format(offset),
        ('i32.const', base),
        value,
    )


binop_opcode = st.sampled_from([
    'add',
    'mul',
    'sub',
    'shl',
    'shr_u',
    'shr_s',
    'xor',
    'or',
    'and',
    # 'i64.div_u',  # triggers division by zero..
    # 'i64.div_s',
])


cmp_opcodes = st.sampled_from([
    "eq",
    "ne",
    "lt_s",
    "lt_u",
    "gt_s",
    "gt_u",
    "le_s",
    "le_u",
    "ge_s",
    "ge_u",
])

i64_extend_opcode = st.sampled_from([
    'i64.extend_i32_s',
    'i64.extend_i32_u',
])

@composite
def i64_binop(draw):
    opcode  ='i64.' + draw(binop_opcode)
    return (opcode, draw(i64_value), draw(i64_value))


@composite
def i64_from_i32(draw):
    opcode = draw(i64_extend_opcode)
    val = draw(i32_value)
    return (opcode, val)


i64_value = i64_const | i64_load() | i64_binop() | i64_from_i32()
i64_expr = i64_value | st.just(('call', '$func2'))

i32_const = st.integers(min_value=-2**31, max_value=2**31-1).map(lambda x: ('i32.const', x))

i32_load_opcodes = st.sampled_from([
    'i32.load',
    'i32.load16_s',
    'i32.load16_u',
    'i32.load8_s',
    'i32.load8_u',
])

i32_store_opcodes = st.sampled_from([
    "i32.store",
    "i32.store8",
    "i32.store16",
])

i64_store_opcodes = st.sampled_from([
    "i64.store",
    "i64.store8",
    "i64.store16",
    "i64.store32",
])

@composite
def i32_load(draw):
    opcode = draw(i32_load_opcodes)
    base = draw(st.integers(min_value=0, max_value=9))
    offset = draw(st.integers(min_value=0, max_value=11))
    return (opcode, 'offset={}'.format(offset), ('i32.const', base))


@composite
def i32_store(draw):
    opcode = draw(i32_store_opcodes)
    value = draw(i32_value)
    base = draw(st.integers(min_value=0, max_value=9))
    offset = draw(st.integers(min_value=0, max_value=11))
    return (
        opcode, 'offset={}'.format(offset),
        ('i32.const', base),
        value,
    )


@composite
def i32_binop(draw):
    opcode = 'i32.' + draw(binop_opcode)
    return (opcode, draw(i32_value), draw(i32_value))


i32_value = i32_const | i32_load() | i32_binop()
i32_expr = i32_value | st.just(('call', '$func3'))


# @given(i64_expr, i32_expr, i64_value, st.binary(min_size=100, max_size=200))
@given(i64_value, st.binary(min_size=30, max_size=40))
@settings(deadline=600, max_examples=400)
def tst_expression_behavior(v64, mem):
    # assume(s != 0)
    # print('code', v64, v32)

    source = ('module',
        # ('func', '$func3', ('result', 'i32'),
        #     v64,
        #     ('i32.wrap_i64',)
        # ),
        # ('func', '$func2', ('result', 'i64'),
        #     expr32,
        #     ('i64.extend_i32_s',),
        # ),
        ('func', ('export', 'my_func'), ('result', 'i64'),
            v64
            # ('i64.const', s),
            # ('i64.const', s),
            # ('i64.add'),
            # ('i64.const', s),
            # ('i64.mul'),
            # ('i64.const', s),
            # ('i64.sub'),
            # ('i64.const', s),
            # ('i64.rem_u'),
        ),
        ('memory', 2),
        ('data', ('i32.const', 0), mem)
    )

    # Create wasm module
    m = Module(source)
    assert_equal_behavior(m)


@given(i64_load(), st.binary(min_size=32, max_size=48))
@settings(deadline=None)
def test_memory_i64_load_behavior(load_op, mem):
    source = ('module',
        ('func', ('export', 'my_func'), ('result', 'i64'),
            load_op
        ),
        ('memory', 1),
        ('data', ('i32.const', 0), mem)
    )

    # Create wasm module
    m = Module(source)
    assert_equal_behavior(m)


@given(i32_load(), st.binary(min_size=32, max_size=48))
@settings(deadline=None)
def test_memory_i32_load_behavior(load_op, mem):
    source = ('module',
        ('func', ('export', 'my_func'), ('result', 'i32'),
            load_op
        ),
        ('memory', 1),
        ('data', ('i32.const', 0), mem)
    )

    m = Module(source)
    assert_equal_behavior(m)


@given(i32_store(), st.binary(min_size=32, max_size=48))
@settings(deadline=None)
def test_memory_i32_store_behavior(store_op, mem):
    source = ('module',
        ('func', ('export', 'my_func'),
            store_op
        ),
        ('memory', ('export', 'mem'), 1),
        ('data', ('i32.const', 0), mem)
    )

    m = Module(source)
    assert_equal_memory(m)


@given(i64_store(), st.binary(min_size=32, max_size=48))
@settings(deadline=None)
def test_memory_i64_store_behavior(store_op, mem):
    source = ('module',
        ('func', ('export', 'my_func'),
            store_op
        ),
        ('memory', ('export', 'mem'), 1),
        ('data', ('i32.const', 0), mem)
    )

    m = Module(source)
    assert_equal_memory(m)


@given(cmp_opcodes, i32_const, i32_const)
@settings(deadline=None)
def test_i32_comparison_behavior(cmp_op, v1, v2):
    opcode = 'i32.' + cmp_op
    source = ('module',
        ('func', ('export', 'my_func'), ('result', 'i32'),
            (opcode, v1, v2)
        ),
    )

    m = Module(source)
    assert_equal_behavior(m)


@given(cmp_opcodes, i64_const, i64_const)
@settings(deadline=None)
def test_i64_comparison_behavior(cmp_op, v1, v2):
    opcode = 'i64.' + cmp_op
    source = ('module',
        ('func', ('export', 'my_func'), ('result', 'i32'),
            (opcode, v1, v2)
        ),
    )

    m = Module(source)
    assert_equal_behavior(m)


@given(st.integers(min_value=0, max_value=0xffff), st.integers(min_value=0, max_value=0xffff))
@settings(deadline=None)
def test_coremark_crc16(v1, v2):
    coremark_wasm_snippet = r"""
    (module
      (func $crc8 (param i32 i32) (result i32)
        local.get 0
        local.get 1
        i32.add)

      (func (export "crc16") (param i32 i32) (result i32)
        local.get 0
        i32.const 16
        i32.shr_u
        local.get 0
        i32.const 65535
        i32.and
        local.get 1
        call $crc8
        call $crc8)
    )
    """
    m = Module(coremark_wasm_snippet)
    py_inst = instantiate(m, {}, target='python')
    native_inst = instantiate(m, {}, target='native')
    res1 = py_inst.exports['crc16'](v1, v2)
    res2 = native_inst.exports['crc16'](v1, v2)
    print('results', res1, 'should be equal to', res2)
    assert res1 == res2


def assert_equal_behavior(m):
    """ Instantiate the module in both python and native.

    Test that both operate the same.
    """
    print(m.to_string())

    # Compile / instantiate:
    py_inst = instantiate(m, {}, target='python')
    native_inst = instantiate(m, {}, target='native')

    # Run both python and x86 variant and compare outputs.
    res1 = py_inst.exports['my_func']()
    res2 = native_inst.exports['my_func']()
    print('results', res1, 'should be equal to', res2)
    assert res1 == res2


def assert_equal_memory(m):
    """ Instantiate the module in both python and native.

    Test that both operate the same.
    """
    print(m.to_string())

    # Compile / instantiate:
    py_inst = instantiate(m, {}, target='python')
    native_inst = instantiate(m, {}, target='native')

    # Run both python and x86 variant
    py_inst.exports['my_func']()
    native_inst.exports['my_func']()

    # Compare memory contents:
    py_mem = py_inst.exports['mem']
    native_mem = native_inst.exports['mem']

    assert py_mem.read(0, 100) == native_mem.read(0, 100)


if __name__ == "__main__":
    test_memory_i64_load_behavior()
    test_memory_i32_load_behavior()
    test_i32_comparison_behavior()
    test_i64_comparison_behavior()
    print('OK.')
