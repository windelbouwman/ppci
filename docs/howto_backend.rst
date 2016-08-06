
How to write a new backend
--------------------------

This section describes how to add a new backend. The best thing to do is
to take a look at existing backends, like the backends for ARM and X86_64.

A backend consists of the following parts:

#. register descriptions
#. instruction descriptions
#. template descriptions
#. architecture description


Register description
~~~~~~~~~~~~~~~~~~~~

A backend must describe what kinds of registers are available. To do this
define for each register class a subclass of :class:`ppci.arch.isa.Register`.

There may be several register classes, for example 8-bit and 32-bit registers.
It is also possible that these classes overlap.

.. code:: python

    from ppci.arch.isa import Register

    class X86Register(Register):
        bitsize=32

    class LowX86Register(Register):
        bitsize=8

    AL = LowX86Register('al', num=0)
    AH = LowX86Register('ah', num=4)
    EAX = X86Register('eax', num=0, aliases(AL, AH))


Architecture description
~~~~~~~~~~~~~~~~~~~~~~~~

