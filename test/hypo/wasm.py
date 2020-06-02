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
    'i64.load8_s',
    'i64.load8_u',
])


@composite
def i64_load(draw):
    opcode = draw(i64_load_opcode)
    base = draw(st.integers(min_value=0, max_value=33))
    offset = draw(st.integers(min_value=0, max_value=34))
    return (opcode, 'offset={}'.format(offset), ('i32.const', base))


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
    'i32.load8_s',
    'i32.load8_u',
])


@composite
def i32_load(draw):
    opcode = draw(i32_load_opcodes)
    base = draw(st.integers(min_value=0, max_value=15))
    offset = draw(st.integers(min_value=0, max_value=17))
    return (opcode, 'offset={}'.format(offset), ('i32.const', base))


@composite
def i32_binop(draw):
    opcode = 'i32.' + draw(binop_opcode)
    return (opcode, draw(i32_value), draw(i32_value))

i32_value = i32_const | i32_load() | i32_binop()
i32_expr = i32_value | st.just(('call', '$func3'))

# @given(i64_expr, i32_expr, i64_value, st.binary(min_size=100, max_size=200))
@given(i64_value, st.binary(min_size=30, max_size=40))
@settings(deadline=600, max_examples=400)
def test_equivalent_behavior(v64, mem):
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
    print(m.to_string())

    # Compile / instantiate:
    py_inst = instantiate(m, {}, target='python')
    native_inst = instantiate(m, {}, target='native')

    # Run both python and x86 variant and compare outputs.
    res1 = py_inst.exports['my_func']()
    res2 = native_inst.exports['my_func']()
    print('results', res1, res2)

    assert res1 == res2


if __name__ == "__main__":
    test_equivalent_behavior()
    print('OK.')
