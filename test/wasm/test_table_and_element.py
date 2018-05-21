"""
Test WASM Table and Element definition classes.
"""

from ppci.api import is_platform_supported, get_current_arch
from ppci.wasm import Module, Table, run_wasm_in_node, has_node
from ppci.wasm.instantiate import instantiate, create_runtime


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_table0():

    assert Table('(table anyfunc)').id == '$0'
    assert Table('(table anyfunc)').min == 0
    assert Table('(table anyfunc)').max == None

    assert Table('(table 1 anyfunc)').id == '$0'
    assert Table('(table 1 anyfunc)').min == 1
    assert Table('(table 1 anyfunc)').max == None

    assert Table('(table 1 2 anyfunc)').id == '$0'
    assert Table('(table 1 2 anyfunc)').min == 1
    assert Table('(table 1 2 anyfunc)').max == 2

    assert Table('(table 3 1 2 anyfunc)').id == 3
    assert Table('(table $xx 1 2 anyfunc)').id == '$xx'
    assert Table('(table 3 1 2 anyfunc)').min == 1
    assert Table('(table 3 1 2 anyfunc)').max == 2


def test_table1():

    # The canonical form
    CODE0 = dedent(r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (table 2 2 anyfunc)
        (start $main)
        (elem (i32.const 0) $f1 $f2)
        (func $f1 (type $2)
            (i32.const 101)
            (call $print)
        )
        (func $f2 (type $2)
            (i32.const 102)
            (call $print)
        )
        (func $main (type $2)
            (i32.const 0)
            (call_indirect $2)
            (i32.const 1)
            (call_indirect $2)
        )
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0

    if is_platform_supported():
        pass

    if True:
        printed_numbers = []
        def print_ln(x: int) -> None:
            print(x)
            printed_numbers.append(x)
        imports = {
            'js': {
                'print_ln': print_ln,
            },
            '_runtime': create_runtime(),
        }
        instantiate(m0, imports, target='python')
        assert [101, 102] == printed_numbers

    if has_node():
        assert run_wasm_in_node(m0, True) == '101\n102'

    # Abbreviation: imported table
    m3 = Module('(module (table $t1 (import "foo" "bar_table1") anyfunc) )')
    assert m3.to_string() == dedent("""
    (module
        (import "foo" "bar_table1" (table $t1 anyfunc))
    )
    """)

    m3 = Module('(module (table (import "foo" "bar_table1") 2 3 anyfunc) )')
    assert m3.to_string() == dedent("""
    (module
        (import "foo" "bar_table1" (table 2 3 anyfunc))
    )
    """)


    # Abbeviation: inline data and unspecified (default) alignment
    CODE1 = r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (table anyfunc (elem $f1 $f2))
        (start $main)
        (func $f1 (type $2)
            (i32.const 101)
            (call $print)
        )
        (func $f2 (type $2)
            (i32.const 102)
            (call $print)
        )
        (func $main (type $2)
            (i32.const 0)
            (call_indirect $2)
            (i32.const 1)
            (call_indirect $2)
        )
    )
    """
    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    test_table0()
    test_table1()
