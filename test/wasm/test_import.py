"""
Test WASM Import definition class.
"""

from ppci.wasm import Module, Import


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_import0():

    # Func
    i = Import('foo', 'bar', 'func', '$func1', ('$type1', ))
    assert i.modname == 'foo' and i.name == 'bar'
    assert i.id == '$func1'
    assert i.to_string() == '(import "foo" "bar" (func $func1 (type $type1)))'

    # Table (default id is omitted as is common)
    i = Import('foo', 'bar', 'table', '$table1', ('funcref', 2, 3))
    assert i.modname == 'foo' and i.name == 'bar'
    assert i.id == '$table1'
    assert i.to_string() == '(import "foo" "bar" (table $table1 2 3 funcref))'
    #
    i = Import('foo', 'bar', 'memory', '$0', (1, None))
    assert i.to_string() == '(import "foo" "bar" (memory 1))'

    # Memory (default id is omitted as is common)
    i = Import('foo', 'bar', 'memory', '$mem1', (1, 2))
    assert i.modname == 'foo' and i.name == 'bar'
    assert i.id == '$mem1'
    assert i.to_string() == '(import "foo" "bar" (memory $mem1 1 2))'
    #
    i = Import('foo', 'bar', 'memory', '$0', (1, None))
    assert i.to_string() == '(import "foo" "bar" (memory 1))'

    # Global (mutable and immutable)
    i = Import('foo', 'bar', 'global', '$global1', ('i32', False))
    assert i.modname == 'foo' and i.name == 'bar'
    assert i.id == '$global1'
    assert i.to_string() == '(import "foo" "bar" (global $global1 i32))'
    #
    i = Import('foo', 'bar', 'global', '$global1', ('i32', True))
    assert i.to_string() == '(import "foo" "bar" (global $global1 (mut i32)))'


def test_import1():

    # The canonical form
    CODE0 = dedent("""
    (module
        (type $bar_func (func))
        (import "foo" "bar_func" (func $bar_func (type $bar_func)))
        (import "foo" "bar_table1" (table $t1 2 funcref))
        (import "foo" "bar_mem1" (memory $m1 1))
        (import "foo" "bar_mem2" (memory $m2 1 2))
        (import "foo" "bar_global" (global $bar_global i32))
    )
    """)
    # (import "foo" "bar_table" (table $bar_table (type $bar_func)))

    # Test main code
    m0 = Module(CODE0)
    print(m0.to_string())
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0

    # Import abbreviations: definitions of func/memory/table/global
    # that are really imports.

    CODE1 = dedent("""
    (module
        (type $bar_func (func))
        (func $bar_func (import "foo" "bar_func") (type $bar_func))
        (table $t1 (import "foo" "bar_table1") 2 funcref)
        (memory $m1 (import "foo" "bar_mem1") 1)
        (memory $m2 (import "foo" "bar_mem2") 1 2)
        (global $bar_global (import "foo" "bar_global") i32)
    )
    """)

    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    test_import0()
    test_import1()
