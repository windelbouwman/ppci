
Code instrumentation
====================

This is a howto on code instrumentation. Code instrumentation is the action
of adding extra code to your program. A good example is function call
tracing. With function call tracing, you can execute a custom action whenever
a function is entered. It is also fun and easy to enter infinite recursions
by doing so.


Lets demonstrate how this works with an example!

Say, we have a simple function, and would like to instrument this code.
So, first define a function in C, called ``my_add``, and turn it into IR-code:

.. doctest:: instrumentation

    >>> import io
    >>> from ppci import api
    >>> source = """
    ... int my_add(int a, int b) { return a + b; }
    ... """
    >>> arch = api.get_arch('arm')
    >>> module = api.c_to_ir(io.StringIO(source), arch)
    >>> api.optimize(module, level=2)
    >>> module.display()
    module main;
    <BLANKLINE>
    global function i32 my_add(i32 a, i32 b) {
      my_add_block0: {
        i32 tmp_3 = a + b;
        return tmp_3;
      }
    <BLANKLINE>
    }

Now comes the cool part, the addition of tracing functionality. Since we
have IR-code, we can add tracing to it. This means the tracing functionality
is target independent!

.. doctest:: instrumentation

    >>> from ppci.irutils.instrument import add_tracer
    >>> add_tracer(module)
    >>> module.display()
    module main;
    <BLANKLINE>
    external procedure trace(ptr);
    <BLANKLINE>
    global function i32 my_add(i32 a, i32 b) {
      my_add_block0: {
        blob<7:1> func_name = literal '6d795f61646400';
        ptr name_ptr = &func_name;
        call trace(name_ptr);
        i32 tmp_3 = a + b;
        return tmp_3;
      }
    <BLANKLINE>
    }

Notice the extra code inserted! Now, we could turn this into machine code
like this:

.. doctest:: instrumentation

    >>> print(api.ir_to_assembly([module], arch))
           section data
           global trace
           type trace func
           section data
           section code
           global my_add
           type my_add func
     my_add:
           push LR, R11
           mov R11, SP
           push R5, R6
           mov R6, R1
           mov R5, R2
     my_add_block0:
           ldr R1, my_add_literal_1
           bl trace
           add R0, R6, R5
           b my_add_epilog
     my_add_epilog:
           pop R5, R6
           pop PC, R11
           ALIGN(4)
     my_add_literal_0:
           db 109
           db 121
           db 95
           db 97
           db 100
           db 100
           db 0
           ALIGN(4)
     my_add_literal_1:
           dcd =my_add_literal_0
           ALIGN(4)
    <BLANKLINE>

Notice here as well the extra call to the ``trace`` function.
