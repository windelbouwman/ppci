
OCaml
=====

.. warning::

    This module is a work in progress.

OCaml is a functional programming language. Its output is bytecode.

This is an exploration on how to compile this bytecode.

Produce bytecode for example by:

.. code:: bash

    $ ocamlc -o test.byte test.ml
    $ python -m ppci.cli.ocaml disassemble test.byte
    $ FUTURE: python -m ppci.cli.ocaml opt test.byte -m m68k


Module
------

.. automodule:: ppci.lang.ocaml
    :members:
