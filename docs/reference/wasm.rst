.. _wasm:

Web Assembly
============

Web Assembly (wasm) is a portable binary format designed for the web.

http://webassembly.org/


Creating a wasm module
----------------------

A WASM :class:`Module <ppci.wasm.Module>` can be created from its text
representation, a corresponding tuple structure, a bytes object or binary file,
or from another Module object:

.. doctest:: wasm

    >>> from ppci import wasm
    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))'
    >>> m1 = wasm.Module(code)
    >>> m2 = wasm.Module(m1.to_bytes())


The :func:`read_wasm() <ppci.wasm.read_wasm>` function is a thin wrapper around the Module constructor.

Exporting a wasm module
-----------------------

A wasm module can be exported to text or binary form:

.. doctest:: wasm

    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))'
    >>> m = wasm.Module(code)
    >>> m.to_string()
    '(module\n    (type $0 (func (result i32)))\n    (func $truth (type $0)\n        (i32.const 42)\n        (return)\n    )\n)\n'
    >>> m.to_bytes()
    b'\x00asm\x01\x00\x00\x00\x01\x05\x01`\x00\x01\x7f\x03\x02\x01\x00\n\x07\x01\x05\x00A*\x0f\x0b'

And can also be "displayed" in these forms:

.. doctest:: wasm

    >>> m.show()
    (module
        (type $0 (func (result i32)))
        (func $truth (type $0)
            (i32.const 42)
            (return)
        )
    )
    <BLANKLINE>
    >>> m.show_bytes()
    00000000  00 61 73 6d 01 00 00 00 01 05 01 60 00 01 7f 03  .asm.......`....
    00000010  02 01 00 0a 07 01 05 00 41 2a 0f 0b              ........A*..


Running wasm
------------

Wasm can be executed in node:

.. code-block:: python

    wasm.run_wasm_in_node(m)


Or in the browser by exporing an html file:

.. code-block:: python

    wasm.export_wasm_example('~/wasm.html', code, m)


Inside a jupyter notebook, the WASM can be run directly:

.. code-block:: python

    wasm.run_wasm_in_notebook(m)


Running in the Python process:

.. doctest:: wasm

    >>> code = '(module (func (export truth) (result i32) (i32.const 42) (return)))'
    >>> m1 = wasm.Module(code)
    >>> from ppci.wasm import instantiate
    >>> loaded = instantiate(m1, {})
    >>> loaded.exports.truth()
    42

Converting between wasm and ir
------------------------------

With the :py:func:`ppci.wasm.wasm_to_ir` class it is possible to translate
wasm code
to ir-code. It is also possible to translate ir-code into wasm with the
:py:func:`ppci.wasm.ir_to_wasm` function.
This allows, for instance, running C3 on the web, or Web Assembly on a microprocessor.


The basic functionality is there, but more work is needed e.g. a stdlib
for this functionality to be generally useful.

.. doctest:: wasm

    >>> from ppci import wasm
    >>> from ppci.wasm.arch import WasmArchitecture
    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))'
    >>> m1 = wasm.Module(code)
    >>> arch = WasmArchitecture()
    >>> ir = wasm.wasm_to_ir(m1, arch.info.get_type_info('ptr'))
    >>> m2 = wasm.ir_to_wasm(ir)


Module reference
----------------

.. automodule:: ppci.wasm
    :members:

.. automodule:: ppci.wasm.instantiate
    :members:
