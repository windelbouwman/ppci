
Llvm
----

.. automodule:: ppci.lang.llvmir
    :members:

Example usage
~~~~~~~~~~~~~

An example usage is the following:

.. code:: bash

    $ llvm-stress | ppci-llc.py -m riscv -o my_object.oj -

Here, the llvm-stress tool generates some random llvm source code, and
this is piped into the ppci-llc.py command, which takes ll code and turns
it into machine code.

Another example is how to use clang together with ppci-llc.py:

.. code:: bash

    $ clang -S -emit-llvm -o - magic2.c | ppci-llc.py -o my_obj.oj -m msp430 -

This will compile the sourcefile magic2.c into my_obj.oj for the msp430 target.
