"""
Playing with WASM by manually composing a WASM module. This demonstrates
three ways to compose a module, using plain text, tuples, and the internal
classes.
"""

from ppci import wasm


## Define WASM module using pure WAT

# This is great if you like writing WASM by hand. Abbreviations are
# automatically resolved (e.g. inline signatures and nested
# instructions).

wa1 = wasm.Module(
    """
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
    )"""
)

# Show text and binary representation of the module
wa1.show()
wa1.show_bytes()


## Define WASM module using tuples

# When programatically generating WAT code, it's usually easier to
# build up a list of instructions as tuples. Abbvreviations can still
# be used.

instructions = [
    ("loop"),
    # print iter
    ("local.get", 0),
    ("call", "$print"),
    # Increase iter
    ("f64.const", 1),
    ("local.get", 0),
    ("f64.add"),
    ("local.tee", 0),
    ("f64.const", 10),
    ("f64.lt"),
    ("br_if", 0),
    ("end"),
]

# And then embed the list of instructions in a module.
# Note how we can even mix string and tuple reprsentations here.

wa2 = wasm.Module(
    # ('import', 'js', 'print_ln', ('func', '$print', ('param', 'f64'))),
    '(import "js" "print_ln" (func $print (param f64)))',
    ("start", "$main"),
    ("func", "$main", ("local", "f64")) + tuple(instructions),
)

# Result is exactly the same!
assert wa2.to_bytes() == wa1.to_bytes()


## Define WASM module using Component instances

# We can also use the internal component classes directly. This offers
# a more direct and explicit way to define a Module, but we can no longer
# use abbreviations or nested instructions.

# One can pass tuple-instructions to a Func object, or embed a list
# of Instructions objects in a tuple representation of a func. But don't
# mix tuples and Instruction objects within a single function.

Instr = wasm.components.Instruction

instructions = [
    Instr("loop", "emptyblock"),
    # write iter
    Instr("local.get", wasm.components.Ref("local", index=0)),
    Instr("call", wasm.components.Ref("func", name="$print", index=0)),
    # Increase iter
    Instr("f64.const", 1),
    Instr("local.get", wasm.components.Ref("local", index=0)),
    Instr("f64.add"),
    Instr("local.tee", wasm.components.Ref("local", index=0)),
    Instr("f64.const", 10),
    Instr("f64.lt"),
    Instr("br_if", wasm.components.Ref("label", index=0)),
    Instr("end"),
]

wa3 = wasm.Module(
    wasm.components.Type("$print_sig", [(0, "f64")], []),
    wasm.components.Type("$main_sig", [], []),
    wasm.components.Import(
        "js",
        "print_ln",
        "func",
        "$print",
        (wasm.components.Ref("type", name="$print_sig", index=0),),
    ),
    wasm.components.Start(wasm.components.Ref("func", name="$main", index=1)),
    wasm.components.Func(
        "$main",
        wasm.components.Ref("type", name="$main_sig", index=1),
        [(None, "f64")],
        instructions,
    ),
)

# Result is exactly the same!
assert wa3.to_bytes() == wa1.to_bytes()


## Recursion ...

# The text representation of a module produces an exact copy
assert wasm.Module(wa1.to_string()).to_bytes() == wa1.to_bytes()

# Using the elements (definitions) of a module to create a new module too
assert wasm.Module(*[d for d in wa1]).to_bytes() == wa1.to_bytes()

# We can reconstruct the module from its binary form
assert wasm.Module(wa1.to_bytes()).to_bytes() == wa1.to_bytes()


## Let's run it

wasm.run_wasm_in_node(wa1)

import webbrowser

wasm.export_wasm_example(__file__[:-3] + ".html", wa1.to_string(), wa1)
webbrowser.open(__file__[:-3] + ".html")
