"""
Test WASM Export definition class.
"""

from ppci.wasm import Module, Export, Ref


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


def test_export0():

    # Func
    e = Export('foo', 'func', Ref('func', name='$func1'))
    assert e.name == 'foo'
    assert e.ref.name == '$func1'
    assert e.to_string() == '(export "foo" (func $func1))'
    # assert e.to_string() == Export(e.to_string()).to_string()

    # Table (default id is omitted as is common)
    e = Export('foo', 'table', Ref('table', name='$table1'))
    assert e.name == 'foo'
    assert e.ref.name == '$table1'
    assert e.to_string() == '(export "foo" (table $table1))'
    # assert e.to_string() == Export(e.to_string()).to_string()

    # Memory (default id is omitted as is common)
    e = Export('foo', 'memory', Ref('memory', name='$mem1'))
    assert e.name == 'foo'
    assert e.ref.name == '$mem1'
    assert e.to_string() == '(export "foo" (memory $mem1))'
    # assert e.to_string() == Export(e.to_string()).to_string()

    # Global (mutable and immutable)
    e = Export('foo', 'global', Ref('global', name='$global1'))
    assert e.name == 'foo'
    assert e.ref.name == '$global1'
    assert e.to_string() == '(export "foo" (global $global1))'
    # assert e.to_string() == Export(e.to_string()).to_string()


def test_export1():

    # The canonical form
    CODE0 = dedent("""
    (module
        (type $sig (func))
        (table $t1 2 funcref)
        (memory $m1 1)
        (global $g1 i32 (i32.const 7))
        (export "bar_table1" (table $t1))
        (export "bar_mem1" (memory $m1))
        (export "bar_global" (global $g1))
        (export "bar_func1" (func $f1))
        (export "bar_func2" (func $f1))
        (func $f1 (type $sig)
        
        )
    )
    """)

    # Test main code
    m0 = Module(CODE0)
    print(m0.to_string())
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0

    # Export abbreviations: definitions of func/memory/table/global
    # that are really exports.

    CODE1 = dedent("""
    (module
        (type $sig (func))
        (table $t1 (export "bar_table1") 2 funcref)
        (memory $m1 (export "bar_mem1") 1)
        (global $g1 (export "bar_global") i32 (i32.const 7))
        (func $f1
            (export "bar_func1") (export "bar_func2")
            (type $sig)
        )
    )
    """)

    m1 = Module(CODE1)
    assert m1.to_string() == CODE0
    assert m1.to_bytes() == b0


if __name__ == '__main__':
    # test_export0()
    test_export1()
