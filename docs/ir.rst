

IR-code
=======

Front ends generate this IR-code. Backends transform it into machine code.

The IR-code is implemented in the ir package.

.. autoclass:: ppci.ir.Module

.. autoclass:: ppci.ir.Function

.. autoclass:: ppci.ir.Block

A block contains a sequence of statements.

.. autoclass:: ppci.ir.Load
.. autoclass:: ppci.ir.Store
.. autoclass:: ppci.ir.Const
.. autoclass:: ppci.ir.Binop
.. autoclass:: ppci.ir.Call
.. autoclass:: ppci.ir.Jump
.. autoclass:: ppci.ir.CJump

