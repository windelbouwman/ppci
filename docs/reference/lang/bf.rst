
.. currentmodule:: ppci.lang.bf

Brainfuck
=========

The compiler has a front-end for
`the brainfuck language <https://en.wikipedia.org/wiki/Brainfuck>`_.
You can use :func:`bf_to_ir` to transform brainfuck code
into IR-code:

.. doctest::

    >>> from ppci.lang.bf import bf_to_ir
    >>> import io
    >>> ir_module = bf_to_ir(io.StringIO('>>ignore.'), 'arm')
    >>> ir_module.display()
    module main;
    <BLANKLINE>
    external procedure bsp_putc(u8);
    <BLANKLINE>
    variable data (30000 bytes aligned at 4)
    <BLANKLINE>
    procedure main() {
      main_block0: {
        blob<4:4> ptr_alloc = alloc 4 bytes aligned at 4;
        ptr ptr_addr = &ptr_alloc;
        i32 one = 1;
        i8 val_inc = cast one;
        ptr ptr_incr = cast one;
        i32 zero = 0;
        ptr zero_ptr = cast zero;
        i8 zero_ptr_0 = cast zero;
        ptr array_max = 30000;
        store zero_ptr, ptr_addr;
        jmp main_block2;
      }
    <BLANKLINE>
      main_block1: {
        exit;
      }
    <BLANKLINE>
      main_block2: {
        ptr ptr_val = load ptr_addr;
        ptr cell_addr = data + ptr_val;
        store zero, cell_addr;
        ptr add = ptr_val + ptr_incr;
        store add, ptr_addr;
        cjmp add == array_max ? main_block1 : main_block2;
      }
    <BLANKLINE>
    }


Reference
---------

.. automodule:: ppci.lang.bf
    :members:

