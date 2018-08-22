"""
Test WASM Type definition class.
"""

from ppci.wasm import Module, Type, run_wasm_in_node, has_node


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_type0():
    t = Type('$foo', [(0, 'i32'), (1, 'i32'), (2, 'f32'), ('$x', 'f32')], ['i32'])
    assert t.to_string() == '(type $foo (func (param i32 i32 f32) (param $x f32) (result i32)))'
    # assert t.params == Type(t.to_string()).params


def test_type1():
    """ Test canoncocal form of import and func and inline typedefs.
    """

    # The canonical form
    CODE0 = dedent("""
    (module
        (type $0 (func (param i32)))
        (type $1 (func (param i32 i32) (result i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $0)))
        (start $main)
        (func $add (type $1)
            (get_local 0)
            (get_local 1)
            (i32.add)
        )
        (func $main (type $2)
            (i32.const 4)
            (i32.const 3)
            (call $add)
            (call $print)
        )
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0
    if has_node():
        assert run_wasm_in_node(m0, True) == '7'

    # Abbreviation: inline typedefs
    CODE1 = """
    (module
        (import "js" "print_ln" (func $print (param i32)))
        (start $main)
        (func $add (param i32 i32) (result i32)
            (get_local 0)
            (get_local 1)
            (i32.add)
        )
        (func $main
            (i32.const 4)
            (i32.const 3)
            (call $add)
            (call $print)
        )
    )
    """
    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


def test_type2():
    """ Test inline typedefs with various number of args and results.
    """

    # Canonical form
    CODE0 = dedent("""
    (module
        (type $0 (func (param i32)))
        (type $1 (func (param i32) (result i32)))
        (type $2 (func (result i32)))
        (type $3 (func))
        (import "js" "print_ln" (func $print (type $0)))
        (start $main)
        (func $test_11 (type $1)
            (i32.const 111)
            (call $print)
            (i32.const 0)
        )
        (func $test_10 (type $0)
            (i32.const 110)
            (call $print)
        )
        (func $test_01 (type $2)
            (i32.const 101)
            (call $print)
            (i32.const 0)
        )
        (func $test_00 (type $3)
            (i32.const 100)
            (call $print)
        )
        (func $main (type $3)
            (i32.const 0)
            (call $test_11)
            (drop)
            (i32.const 0)
            (call $test_10)
            (call $test_01)
            (drop)
            (call $test_00)
        )
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    if has_node():
        assert run_wasm_in_node(m0, True) == '111\n110\n101\n100'

    # Abbreviated
    CODE1 = """
    (module
        (import "js" "print_ln" (func $print (param i32)))
        (start $main)
        (func $test_11 (param i32) (result i32)
            (i32.const 111)
            (call $print)
            (i32.const 0)
        )
        (func $test_10 (param i32)
            (i32.const 110)
            (call $print)
        )
        (func $test_01 (result i32)
            (i32.const 101)
            (call $print)
            (i32.const 0)
        )
        (func $test_00
            (i32.const 100)
            (call $print)
        )
        (func $main
            (i32.const 0) (call $test_11) (drop)
            (i32.const 0) (call $test_10)
            (call $test_01) (drop)
            (call $test_00)
        )
    )
    """

    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    test_type0()
    test_type1()
    test_type2()
