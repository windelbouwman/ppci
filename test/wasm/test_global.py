"""
Test WASM Global definition class.
"""

from ppci.wasm import Module, Global, Instruction, run_wasm_in_node, has_node


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_global0():

    g = Global('$foo', 'i32', False, [Instruction('(i32.const 7)')])
    assert g.to_string() == '(global $foo i32 (i32.const 7))'
    # TODO: do we still wish to support this:
    # assert Global(g.to_string()).to_string() == g.to_string()

    g = Global('$foo', 'i32', True, [Instruction('(i32.const 7)')])
    assert g.to_string() == '(global $foo (mut i32) (i32.const 7))'
    # TODO: do we still wish to support this:
    # assert Global(g.to_string()).to_string() == g.to_string()


def test_global1():

    CODE0 = dedent(r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (global $foo i32 (i32.const 7))
        (start $main)
        (func $main (type $2)
            (get_global $foo)
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


if __name__ == '__main__':
    test_global0()
    test_global1()
