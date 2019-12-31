

Finding loops
=============

To detect program structure like loops and if statements from basic blocks,
one can use algorithms in these classes to find them.

In the below example an ir function is defined, and then the loops are
detected.

.. doctest::

    >>> import io
    >>> from ppci.graph.relooper import find_structure, print_shape
    >>> from ppci.irutils import read_module, verify_module
    >>> ir_source = """
    ... module demo;
    ... global function i32 inc(i32 a, i32 b) {
    ...   inc_block0: {
    ...     jmp inc_block1;
    ...   }
    ...   inc_block1: {
    ...     i32 x = phi inc_block0: a, inc_block1: result;
    ...     i32 result = x + b;
    ...     cjmp result > b ? inc_block2 : inc_block1;
    ...   }
    ...   inc_block2: {
    ...     return result;
    ...   }
    ... }
    ... """
    >>> ir_module = read_module(io.StringIO(ir_source))
    >>> verify_module(ir_module)
    >>> ir_module.stats()
    'functions: 1, blocks: 3, instructions: 5'
    >>> ir_function = ir_module.get_function('inc')
    >>> shape, _ = find_structure(ir_function)
    >>> print_shape(shape)
       code: CFG-node(inc_block0)
       loop
          if-then CFG-node(inc_block1)
             code: CFG-node(inc_block2)
          else
             Continue-shape 0
          end-if
       end-loop

As can be seen, the program contains one loop.


Reference
---------

.. automodule:: ppci.graph.relooper
    :members:

