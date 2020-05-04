"""
Test WASM Module class.
"""

from ppci import wasm


def dedent(code):
    return '\n'.join(line[4: ]for line in code.splitlines()).strip() + '\n'


# TODO: check how (loop) is handled. Is this a loop with no contents? Or is
# it the start of a loop?
def tst_module1():

    instructions1 = [
        ('loop', None, 'emptyblock'),
            # print iter
            ('local.get', 0), ('call', '$print'),
            # Increase iter
            ('f64.const', 1), ('local.get', 0), ('f64.add', ),
            ('local.tee', 0), ('f64.const', 10),
            ('f64.lt', ), ('br_if', 0),
        ('end', ),
        ]
    
    instructions2 = [
        ('loop', 'emptyblock'),
            # write iter
            ('local.get', 0),
            ('call', '$print'),
            # Increase iter
            ('f64.const', 1),
            ('local.get', 0),
            ('f64.add', ),
            ('local.tee', 0),
            ('f64.const', 10),
            ('f64.lt', ),
            ('br_if', 0),
        ('end', ),
        ]

    CODE0 = dedent("""
    (module
        (type $print (func (param f64)))
        (type $1 (func))
        (import "js" "print_ln" (func $print (type $print)))
        (start $main)
        (func $main (type $1) (local f64)
            loop
                (local.get 0)
                (call $print)
                (f64.const 1)
                (local.get 0)
                (f64.add)
                (local.tee 0)
                (f64.const 10)
                (f64.lt)
                (br_if 0)
            (end)
        )
    )
    """)

    # ----- Test main code

    m0 = wasm.Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    if wasm.has_node():
        assert wasm.run_wasm_in_node(m0, True) == '0\n1\n2\n3\n4\n5\n6\n7\n8\n9'


    # ----- Abbreviated text

    m1 = wasm.Module("""
        (module
            (import "js" "print_ln" (func $print (param f64)))
            (start $main)
            (func $main (local f64)
                (loop
                    ;; print iter
                    (local.get 0) (call $print)
                    ;; increase iter
                    (f64.const 1) (local.get 0) (f64.add)
                    (local.tee 0) (f64.const 10)
                    (f64.lt) (br_if 0)
                )
            )
        )""")

    assert m1.to_bytes() == b0

    # ------ Tuples with tuple instructions

    m2 = wasm.Module(
        '(import "js" "print_ln" (func $print (param f64)))',
        ('start', '$main'),
        ('func', '$main', ('local', 'f64')) + tuple(instructions1),
    )

    assert m2.to_bytes() == b0

    # ------ Tuples with Instruction instances

    m3 = wasm.Module(
        '(import "js" "print_ln" (func $print (param f64)))',
        ('start', '$main'),
        ('func', '$main', ('local', 'f64')) + tuple(instructions2),
    )

    assert m3.to_bytes() == b0

    # ------ Definition instances with tuple instructions

    m4 = wasm.Module(
        wasm.Type('$print_sig', [(0, 'f64')], []),
        wasm.Type('$main_sig', [], []),
        wasm.Import('js', 'print_ln', 'func', '$print', ('$print_sig', ), ),
        wasm.Start('$main'),
        wasm.Func('$main', wasm.Ref('type', name='$main_sig'), [(None, 'f64')], instructions1),
    )

    assert m4.to_bytes() == b0

    # ------ Definition instances with Instruction instances

    m5 = wasm.Module(
        wasm.Type('$print_sig', [(0, 'f64')], []),
        wasm.Type('$main_sig', [], []),
        wasm.Import('js', 'print_ln', 'func', '$print', ('$print_sig', ), ),
        wasm.Start('$main'),
        wasm.Func('$main', wasm.Ref('type', name='$main_sig'), [(None, 'f64')], instructions2),
    )

    assert m5.to_bytes() == b0

    # ------ From module elements

    m6 = wasm.Module(*m0)
    assert m6.to_bytes() == b0

    # ------ to_string()

    m7 = wasm.Module(m0.to_string())
    assert m7.to_bytes() == b0

    # ------ to_bytes()

    m8 = wasm.Module(b0)
    assert m8.to_bytes() == b0


def test_module_id():

    m1 = wasm.Module("(module)")
    m2 = wasm.Module("(module $foo)")
    m3 = wasm.Module("(module $bar (func $spam))")

    assert m1.id is None
    assert len(m1.definitions) == 0
    assert m1.to_string() == '(module)\n'

    assert m2.id == '$foo'
    assert m2.to_string() == '(module $foo)\n'
    assert len(m2.definitions) == 0

    assert m3.id == '$bar'
    assert len(m3.definitions) == 2  # Type and func


if __name__ == '__main__':
    test_module1()
    test_module_id()
