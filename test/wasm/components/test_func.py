"""
Test WASM Func definition class.
"""

from ppci.wasm import Module, Func, run_wasm_in_node, has_node, Ref
from ppci.wasm import instantiate


def dedent(code):
    return "\n".join(line[4:] for line in code.splitlines()).strip() + "\n"


def test_func0():
    f = Func(
        "$foo",
        Ref("type", name="$sig"),
        [(None, "i32"), ("$local1", "f32")],
        [],
    )
    assert (
        f.to_string()
        == "(func $foo (type $sig)\n  (local i32) (local $local1 f32)\n)"
    )

    # Locals can be (and are) combined
    f = Func(
        "$foo", Ref("type", name="$sig"), [(None, "i32"), (None, "f32")], []
    )
    assert f.to_string() == "(func $foo (type $sig)\n  (local i32 f32)\n)"


def test_func1():
    # The canonical form
    CODE0 = dedent(
        """
    (module
      (type $0 (func (param i32)))
      (type $1 (func (param i32 i32) (result i32)))
      (type $2 (func))
      (import "js" "print_ln" (func $print (type $0)))
      (start $main)
      (func $add (type $1)
        local.get 0
        local.get 1
        i32.add)
      (func $main (type $2)
        (local $foo i32)
        i32.const 4
        i32.const 3
        call $add
        local.set $foo
        local.get $foo
        call $print)
    )
    """
    )

    # Test main code
    m0 = Module(CODE0)
    assert m0.to_string() == CODE0

    b0 = m0.to_bytes()
    assert Module(b0).to_bytes() == b0

    printed_numbers = []

    def print_ln(x: int) -> None:
        printed_numbers.append(x)

    imports = {
        "js": {
            "print_ln": print_ln,
        },
    }
    instantiate(m0, imports=imports, target="python")
    assert printed_numbers == [7]

    if has_node():
        assert run_wasm_in_node(m0, True) == "7"

    # Abbreviation: inline typedefs
    CODE1 = """
    (module
        (import "js" "print_ln" (func $print (param i32)))
        (start $main)
        (func $add (param i32 i32) (result i32)
            (local.get 0)
            (local.get 1)
            (i32.add)
        )
        (func $main (local $foo i32)
            (local.set $foo
                (call $add
                    (i32.const 4)
                    (i32.const 3)
                )
            )
            (call $print
                (local.get $foo)
            )
        )
    )
    """
    m1 = Module(CODE1)
    assert m1.to_string() == CODE0  # look at the indentation!
    assert m1.to_bytes() == b0


if __name__ == "__main__":
    test_func0()
    test_func1()
