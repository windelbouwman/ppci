.. _wasm:

Web assembly
============

Web assembly (wasm) is a portable binary format designed for the web.

http://webassembly.org/

With the :py:func:`ppci.irs.wasm.wasm_to_ir` class it is possible to translate
wasm code
to ir-code. It is also possible to translate ir-code into wasm with the
:py:func:`ppci.irs.wasm.ir_to_wasm` function.

.. doctest::

    >>> import io
    >>> from ppci import api
    >>> from ppci.irs.wasm import wasm_to_ir, read_wasm
    >>> f = io.BytesIO(bytes.fromhex(
    ... '0061736d0100000001060160017f017f'
    ... '03020100070c01086d61696e5f666163'
    ... '00000a190117002000410148047f4101'
    ... '052000200041016b10006c0b0b'))
    >>> wasm_module = read_wasm(f)
    >>> wasm_module
    <WASM-Module>
    >>> ir_module = wasm_to_ir(wasm_module)
    >>> obj = api.ir_to_object([ir_module], 'xtensa')
    >>> print(obj)  # doctest: +ELLIPSIS
    CodeObject of ... bytes


Module reference
----------------

.. automodule:: ppci.irs.wasm
    :members:
