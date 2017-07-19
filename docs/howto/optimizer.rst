
How to write an optimizer
-------------------------

This section will dive into the pecularities on how to implement an optimizer
scheme. The optimizer will be an IR optimizer, in the sense
that is transforms IR-code into new (and improved) IR-code. This makes the
optimizer both programming language and target architecture independent.

The optimization
~~~~~~~~~~~~~~~~

The optimizer we will implement in this example is an optimization that
deletes redundant branching. For example, in the following code, branch
`b` is never taken:

.. code::

    module optimizable;

    function i32 add(i32 z) {
      entry: {
        i32 x = 1;
        i32 y = 2;
        cjmp x < y ? a : b;
      }
      a: {
        jmp c;
      }
      b: {
        jmp c;
      }
      c: {
        return x;
      }
    }


It can be easily seen that `b` is never jumped to, because `x < y` is always
true. Time to write an optimization that simplifies this!


The implementation
~~~~~~~~~~~~~~~~~~

To implement an optimalisation, the :class:`ppci.opt.transform.ModulePass`
must be subclassed.
For this example, :class:`ppci.opt.transform.InstructionPass` will be used.


.. testcode:: cjmp

    import operator
    from ppci.opt.transform import InstructionPass
    from ppci import ir

    class SimpleComparePass(InstructionPass):
        def on_instruction(self, instruction):
            if isinstance(instruction, ir.CJump) and \
                    isinstance(instruction.a, ir.Const) and \
                    isinstance(instruction.b, ir.Const):
                a = instruction.a.value
                b = instruction.b.value
                mp = {
                    '==': operator.eq,
                    '<': operator.lt, '>': operator.gt,
                    '>=': operator.ge, '<=': operator.le,
                    '!=': operator.ne
                    }
                if mp[instruction.cond](a, b):
                    label = instruction.lab_yes
                else:
                    label = instruction.lab_no
                block = instruction.block
                block.remove_instruction(instruction)
                block.add_instruction(ir.Jump(label))
                instruction.delete()

The implementation first checks if the instruction is a conditional jump
and if both inputs are constant. Then the constants are compared using
the operator module. Finally a :class:`ppci.ir.Jump` instruction is created.
This instruction is added to the block after the :class:`ppci.ir.CJump`
instruction is removed.

First load the IR-module from file. To do this, first create an in memory
file with io.StringIO. Then load this file with :class:`ppci.irutils.Reader`.

.. doctest:: cjmp

    >>> import io
    >>> f = io.StringIO("""
    ... module optimizable;
    ... function i32 add(i32 z) {
    ...   entry: {
    ...     i32 x = 1;
    ...     i32 y = 2;
    ...     cjmp x < y ? a : b;
    ...   }
    ...   a: {
    ...     jmp c;
    ...   }
    ...   b: {
    ...     jmp c;
    ...   }
    ...   c: {
    ...     return x;
    ...   }
    ... }
    ... """)
    >>> from ppci import irutils
    >>> mod = irutils.Reader().read(f)
    >>> print(mod)
    module optimizable

Now run the optimizer pass:

.. doctest:: cjmp

    >>> opt_pass = SimpleComparePass()
    >>> opt_pass.run(mod)

Next delete all unreachable blocks to make sure the module is valid again:

.. doctest:: cjmp

    >>> mod.functions[0].delete_unreachable()

Now print the optimized module:

.. doctest:: cjmp
    :options: +REPORT_UDIFF

    >>> f2 = io.StringIO()
    >>> irutils.Writer(f2).write(mod)
    >>> print(f2.getvalue())
    module optimizable;
    <BLANKLINE>
    function i32 add(i32 z) {
      entry: {
        i32 x = 1;
        i32 y = 2;
        jmp a;
      }
    <BLANKLINE>
      a: {
        jmp c;
      }
    <BLANKLINE>
      c: {
        return x;
      }
    <BLANKLINE>
    }
    <BLANKLINE>

This optimization is implemented in :class:`ppci.opt.cjmp.CJumpPass`.
