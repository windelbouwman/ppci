
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
    global variable data (30000 bytes aligned at 4)
    <BLANKLINE>
    global procedure main() {
      main_block0: {
        blob<4:4> ptr_alloc = alloc 4 bytes aligned at 4;
        ptr ptr_addr = &ptr_alloc;
        i32 num = 1;
        i8 val_inc = cast num;
        ptr ptr_incr = cast num;
        i32 num_0 = 0;
        ptr zero_ptr = cast num_0;
        i8 zero_ptr_1 = cast num_0;
        ptr num_2 = 30000;
        store zero_ptr, ptr_addr;
        jmp main_block2;
      }
    <BLANKLINE>
      main_block1: {
        exit;
      }
    <BLANKLINE>
      main_block2: {
        ptr tmp_load = load ptr_addr;
        ptr tmp = data + tmp_load;
        store num_0, tmp;
        ptr tmp_3 = tmp_load + ptr_incr;
        store tmp_3, ptr_addr;
        cjmp tmp_3 == num_2 ? main_block1 : main_block2;
      }
    <BLANKLINE>
    }


Reference
---------

.. automodule:: ppci.lang.bf
    :members:

