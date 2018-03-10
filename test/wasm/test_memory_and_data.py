"""
Test WASM Memory and Data definition classes.
"""

from ppci.wasm import Module, Memory, Instruction, run_wasm_in_node


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_memory_instructions():
    assert Instruction('(i32.load)').to_string() == '(i32.load align=2)'
    assert Instruction('(i32.load8_u)').to_string() == '(i32.load8_u align=0)'
    assert Instruction('(i32.load16_u)').to_string() == '(i32.load16_u align=1)'

    assert Instruction('(i32.load align=2 offset=3)').to_string() == '(i32.load align=2 offset=3)'
    assert Instruction('(i32.load8_u align=2 offset=3)').to_string() == '(i32.load8_u align=2 offset=3)'
    assert Instruction('(i32.load16_u offset=3)').to_string() == '(i32.load16_u align=1 offset=3)'


def test_memory0():

    assert Memory('(memory 1)').id == '$0'
    assert Memory('(memory 1)').min == 1
    assert Memory('(memory 1)').max == None

    assert Memory('(memory 1 2)').id == '$0'
    assert Memory('(memory 1 2)').min == 1
    assert Memory('(memory 1 2)').max == 2

    assert Memory('(memory 3 1 2)').id == 3
    assert Memory('(memory $xx 1 2)').id == '$xx'
    assert Memory('(memory 3 1 2)').min == 1
    assert Memory('(memory 3 1 2)').max == 2


def test_memory1():

    # The canonical form
    CODE0 = dedent(r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (memory 1 1)
        (start $main)
        (func $main (type $2)
            (i32.const 0)
            (i32.load8_u align=0)
            (call $print)
            (i32.const 1)
            (i32.load8_u align=0)
            (call $print)
        )
        (data (i32.const 0) "\04\03\02")
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0
    assert run_wasm_in_node(m0, True) == '4\n3'

    # Abbreviation: imported memory
    m3 = Module('(module (memory $m1 (import "foo" "bar_mem1") 1) )')
    assert m3.to_string() == dedent("""
    (module
        (import "foo" "bar_mem1" (memory $m1 1))
    )
    """)

    m3 = Module('(module (memory (import "foo" "bar_mem1") 2 3) )')
    assert m3.to_string() == dedent("""
    (module
        (import "foo" "bar_mem1" (memory 2 3))
    )
    """)


    # Abbeviation: inline data and unspecified (default) alignment
    CODE1 = r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (memory (data "\04\03\02"))
        (start $main)
        (func $main (type $2)
            (i32.const 0)
            (i32.load8_u)
            (call $print)
            (i32.const 1)
            (i32.load8_u)
            (call $print)
        )
    )
    """
    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    test_memory_instructions()
    test_memory0()
    test_memory1()
