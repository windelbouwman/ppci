
Dealing with webassembly
========================

In this tutorial we will see the possible ways to use web assembly.

Compiling wasm to native code
-----------------------------

The first possible usage is to take a wasm module and compile it to
native code. The idea is to take wasm code and compile it to native code.

First lets create some wasm code by using wasmfiddle:

https://wasdk.github.io/WasmFiddle/

.. code:: c

   int main() {
     return 42;
   }


The wasm output of this is:

.. code::

    (module
      (table 0 anyfunc)
      (memory $0 1)
      (export "memory" (memory $0))
      (export "main" (func $main))
      (func $main (result i32)
        (i32.const 42)
      )
    )

Download this wasm file from wasm fiddle to your local drive. Now you
can compile it to for example native riscv code:

.. code:: bash

    $ python -m ppci.cli.wasmcompile -v program.wasm -m riscv -O 2 -S
    $ cat f.out
        .section data
        .section code
    main:
        sw x1, -8(x2)
        sw x8, -12(x2)
        mv x8, x2
        addi x2, x2, -12
        addi x2, x2, 0
    block1:
        addi x10, x0, 42
        j main_epilog
    main_epilog:
        addi x2, x2, 0
        addi x2, x2, 12
        lw x8, -12(x2)
        lw x1, -8(x2)
        jalr x0,x1, 0
        .align 4

In this example we compiled C code with one compiler to wasm and took
this wasm and compiled it to riscv code using ppci.

Please see :ref:`WebAssembly<wasm>` for the python api for using webassembly.
