"""
Basic instruction tests, like nesting.
"""

from ppci.wasm import Module, run_wasm_in_node


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_instructions1():
    """ Test canoncocal form of import and func and inline typedefs.
    """

    # The canonical form
    CODE0 = dedent("""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (start $main)
        (func $main (type $2)
            (i32.const 1)
            (if)
                (i32.const 4)
                (i32.const 3)
                (i32.add)
                (call $print)
            (else)
                (i32.const 5)
                (call $print)
            (end)
        )
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0
    assert run_wasm_in_node(m0, True) == '7'


    # Variant 1 - no inentation, nested test for if
    CODE1 = dedent("""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (start $main)
        (func $main (type $2)
            (if (i32.const 1))
            (i32.const 4)
            (i32.const 3)
            (i32.add)
            (call $print)
            (else)
            (i32.const 5)
            (call $print)
            (end)
        )
    )
    """)

    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0

    # Variant 2 - nesting all the way
    CODE2 = dedent("""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (start $main)
        (func $main (type $2)
            (if (i32.const 1)
                (i32.const 4)
                (i32.const 3)
                (i32.add)
                (call $print)
            (else)
                (i32.const 5)
                (call $print)
            )
        )
    )
    """)

    m2 = Module(CODE2)
    assert m2.to_string() == CODE0
    assert m2.to_bytes() == b0

    # Variant 3 - leave out the else clause
    # This is described as an "abbreviation", but it seems that we don't
    # have to always output an else clause in binary form either.
    CODE3 = dedent("""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (start $main)
        (func $main (type $2)
            (if (i32.const 1)
                (i32.const 4)
                (i32.const 3)
                (i32.add)
                (call $print)
            )
        )
    )
    """)

    m3 = Module(CODE3)
    assert m3.to_string() != CODE0
    assert m3.to_bytes() != b0
    assert run_wasm_in_node(m3, True) == '7'


if __name__ == '__main__':
    test_instructions1()
