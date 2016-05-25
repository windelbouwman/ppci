

IR-code
=======

The purpose of an intermediate representation (IR) of a program is to decouple
the implementation of a front-end from the implementation of a back-end. That
is,
front ends generate IR-code, optimizers optimize this code and lastly backends
transform it into machine code or something else.

A good IR has several characteristics:

- It should be simple enough for front-ends to generate code.
- It should be rich enough to exploit the target instructions best.

The IR in the ppci.ir module has the following properties:

- It is
  `static single assignment form <https://en.wikipedia.org/wiki/Static_single_assignment_form>`_.
  Meaning a value can only
  be assigned once, and is then never changed. This has several advantages.
- It contains only basic types. Structures, arrays and void types are not
  represented.


Top level structure
-------------------

The IR-code is implemented in the ir package.

.. autoclass:: ppci.ir.Module
    :members: variables, functions, add_variable

.. autoclass:: ppci.ir.Variable

.. autoclass:: ppci.ir.SubRoutine
    :members: add_block, remove_block

.. autoclass:: ppci.ir.Procedure

.. autoclass:: ppci.ir.Function

.. autoclass:: ppci.ir.Block
    :members: add_instruction, remove_instruction,
              is_empty, is_closed,
              predecessors, successors

Types
-----

Only simple types are available.

.. autodata:: ppci.ir.ptr
    :annotation:

.. autodata:: ppci.ir.i64
    :annotation:

.. autodata:: ppci.ir.i32
    :annotation:

.. autodata:: ppci.ir.i16
    :annotation:

.. autodata:: ppci.ir.i8
    :annotation:

.. autodata:: ppci.ir.u64
    :annotation:

.. autodata:: ppci.ir.u32
    :annotation:

.. autodata:: ppci.ir.u16
    :annotation:

.. autodata:: ppci.ir.u8

.. autodata:: ppci.ir.f64
    :annotation:

.. autodata:: ppci.ir.f32
    :annotation:


Instructions
------------

The following instructions are available.

**Memory instructions**

.. autoclass:: ppci.ir.Load
.. autoclass:: ppci.ir.Store
.. autoclass:: ppci.ir.Alloc

**Data instructions**

.. autoclass:: ppci.ir.Const
.. autoclass:: ppci.ir.Binop
.. autoclass:: ppci.ir.Cast

**Control flow instructions**

.. autoclass:: ppci.ir.ProcedureCall
.. autoclass:: ppci.ir.FunctionCall
.. autoclass:: ppci.ir.Jump
.. autoclass:: ppci.ir.CJump
.. autoclass:: ppci.ir.Return
.. autoclass:: ppci.ir.Exit

**Other**

.. autoclass:: ppci.ir.Phi
.. autoclass:: ppci.ir.Undefined

Abstract instruction classes
----------------------------

There are some abstract instructions, which cannot be used directly but
serve as base classes for other instructions.

.. autoclass:: ppci.ir.Instruction
    :members: function

.. autoclass:: ppci.ir.Value
    :members: is_used

.. autoclass:: ppci.ir.FinalInstruction
