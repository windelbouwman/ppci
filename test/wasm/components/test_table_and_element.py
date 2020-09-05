"""
Test WASM Table and Element definition classes.
"""

from ppci.api import is_platform_supported, get_current_arch
from ppci.wasm import Module, Table, run_wasm_in_node, has_node
from ppci.wasm import instantiate
from ppci.utils.reporting import html_reporter


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def tst_table0():

    assert Table('(table funcref)').id == '$0'
    assert Table('(table funcref)').min == 0
    assert Table('(table funcref)').max == None

    assert Table('(table 1 funcref)').id == '$0'
    assert Table('(table 1 funcref)').min == 1
    assert Table('(table 1 funcref)').max == None

    assert Table('(table 1 2 funcref)').id == '$0'
    assert Table('(table 1 2 funcref)').min == 1
    assert Table('(table 1 2 funcref)').max == 2

    assert Table('(table 3 1 2 funcref)').id == 3
    assert Table('(table $xx 1 2 funcref)').id == '$xx'
    assert Table('(table 3 1 2 funcref)').min == 1
    assert Table('(table 3 1 2 funcref)').max == 2


def test_table1():

    # The canonical form
    CODE0 = dedent(r"""
    (module
      (type $print (func (param i32)))
      (type $2 (func))
      (import "js" "print_ln" (func $print (type $print)))
      (table $0 2 2 funcref)
      (start $main)
      (elem i32.const 0 $f1 $f2)
      (func $f1 (type $2)
        i32.const 101
        call $print)
      (func $f2 (type $2)
        i32.const 102
        call $print)
      (func $main (type $2)
        i32.const 0
        call_indirect (type $2)
        i32.const 1
        call_indirect (type $2))
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0

    html_report = 'table_and_element_compilation_report.html'
    with html_reporter(html_report) as reporter:
        printed_numbers = []
        def print_ln(x: int) -> None:
            printed_numbers.append(x)
        imports = {
            'js': {
                'print_ln': print_ln,
            },
        }
        instantiate(m0, imports=imports, target='python', reporter=reporter)
        assert [101, 102] == printed_numbers

        if is_platform_supported():
            printed_numbers = []
            def print_ln(x: int) -> None:
                printed_numbers.append(x)
            imports = {
                'js': {
                    'print_ln': print_ln,
                },
            }
            instantiate(m0, imports=imports, target='native', reporter=reporter)
            assert [101, 102] == printed_numbers

    if has_node():
        assert run_wasm_in_node(m0, True) == '101\n102'

    # Abbreviation: imported table
    m3 = Module('(module (table $t1 (import "foo" "bar_table1") funcref) )')
    assert m3.to_string() == dedent("""
    (module
      (import "foo" "bar_table1" (table $t1 funcref))
    )
    """)

    m3 = Module('(module (table (import "foo" "bar_table1") 2 3 funcref) )')
    assert m3.to_string() == dedent("""
    (module
      (import "foo" "bar_table1" (table 2 3 funcref))
    )
    """)


    # Abbeviation: inline data and unspecified (default) alignment
    CODE1 = r"""
    (module
        (type $print (func (param i32)))
        (type $2 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (table funcref (elem $f1 $f2))
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
            (call_indirect (type $2))
            (i32.const 1)
            (call_indirect (type $2))
        )
    )
    """
    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    tst_table0()
    test_table1()
