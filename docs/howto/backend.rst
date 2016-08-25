
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

.. testcode::

    from ppci.arch.encoding import Register

    class X86Register(Register):
        bitsize=32

    class LowX86Register(Register):
        bitsize=8

    AL = LowX86Register('al', num=0)
    AH = LowX86Register('ah', num=4)
    EAX = X86Register('eax', num=0, aliases=(AL, AH))


Instruction description
~~~~~~~~~~~~~~~~~~~~~~~

An important part of the backend is the definition of instructions. Every
instruction for a specific machine derives from
:class:`ppci.arch.encoding.Instruction`.


Lets take the nop example of stm8. This instruction can be defined like this:

.. testcode::

    from ppci.arch.token import Token, bit_range
    from ppci.arch.encoding import Instruction, Syntax, FixedPattern

    class Stm8Token(Token):
        def __init__(self):
            super().__init__('>B')

        opcode = bit_range(0, 8)

    class Nop(Instruction):
        syntax = Syntax(['nop'])
        tokens = [Stm8Token]
        patterns = [FixedPattern('opcode', 0x9d)]


This code snippet first defines a token. A token byte sized thing that can
be encoded. It typically has certain fields that are described in isa manual.
In this case the token is 8 bits wide, and has one field called 'opcode'.

Next, the nop instruction is defined. It is a subclass of Instruction and
has a syntax of 'nop'. The syntax is used for creating a nice string
representation of the object, but also during parsing of assembly code.
The tokens contains a list of what tokens this instruction contains.

Finally the patterns attribute contains a list of patterns. In this case
the opcode field is set with the fixed pattern 0x9d.



Instructions are also usable directly, like this:

.. doctest::

    >>> from ppci.arch.x86_64.instructions import Ret
    >>> i = Ret()
    >>> i.encode()
    b'\xc3'


When an instruction is defined, it should be added to an isa. This can be
done like this:

.. testcode::

    from ppci.arch.isa import Isa
    my_isa = Isa()




Architecture description
~~~~~~~~~~~~~~~~~~~~~~~~

