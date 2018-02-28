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
    
..doctest::
    
    >>> from ppci.import wasm
    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))'
    >>> m1 = wasm.Module(code)
    >>> m2 = wasm.Module(m1.to_bytes())


The :func:`read_wasm() <ppci.wasm.read_wasm>` function is a thin wrapper around the Module constructor.

Exporting a wasm module
-----------------------

A wasm module can be exported to text or binary form:
    
.. code-block:: python
    
    >>> from ppci import wasm
    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))'
    >>> m = wasm.Module(code)
    >>> m.to_string()
    '(module ...)'
    >>> m.to_bytes()
    b'\x00asm\x01\x00\x00 ...'

And can also be "displayed" in these forms:

.. code-block:: python
    
    >>> m.show()
    >>> m.show_bytes() 


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


Todo: running in the Python process ...


Converting between wasm and ir
------------------------------

With the :py:func:`ppci.wasm.wasm_to_ir` class it is possible to translate
wasm code
to ir-code. It is also possible to translate ir-code into wasm with the
:py:func:`ppci.wasm.ir_to_wasm` function.
This allows, for instance, running C3 on the web, or Web Assembly on a microprocessor.


The basic functionality is there, but more work is needed e.g. a stdlib
for this functionality to be generally useful.

.. code-block:: python

    >>> from ppci import wasm
    >>> code = '(module (func $truth (result i32) (i32.const 42) (return)))' 
    >>> m1 = wasm.Module(code)
    >>> ir = wasm.wasm2ppci(m1)
    >>> m2 = wasm.ppci2wasm(ir)


Module reference
----------------

.. automodule:: ppci.wasm
    :members:
