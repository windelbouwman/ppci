
Web assembly
============

Web assembly (wasm) is a portable binary format designed for the web.

http://webassembly.org/

With the Wasm2PpciCompiler class it is possible to translate wasm code
to native machine code.

.. warning::

    Example to be added and doctested below.


.. code:: python

    >>> import api
    >>> from ppci.irs.wasm import wasm_to_ppci, load_wasm
    >>> wasm_module = load_wasm('demo.wast')
    >>> ir_module = wasm_to_ppci(wasm_module)
    >>> obj = api.ir_to_code(ir_module, 'msp430')
    >>> print(obj)
    ...


Module reference
----------------

.. autoclass:: ppci.irs.wasm.wasm2ppci.Wasm2PpciCompiler
    :members:
