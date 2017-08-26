
How to write a new backend
==========================

This section describes how to add a new backend. The best thing to do is
to take a look at existing backends, like the backends for ARM and X86_64.

A backend consists of the following parts:

#. register descriptions
#. instruction descriptions
#. template descriptions
#. Function calling machinery
#. architecture description


Register description
--------------------

A backend must describe what kinds of registers are available. To do this
define for each register class a subclass of :class:`ppci.arch.isa.Register`.

There may be several register classes, for example 8-bit and 32-bit registers.
It is also possible that these classes overlap.

.. testcode::

    from ppci.arch.encoding import Register

    class X86Register(Register):
        bitsize = 32

    class LowX86Register(Register):
        bitsize = 8

    AL = LowX86Register('al', num=0)
    AH = LowX86Register('ah', num=4)
    EAX = X86Register('eax', num=0, aliases=(AL, AH))


Tokens
------

Tokens are the basic blocks of complete instructions. They correspond to
byte sequences of parts of instructions. Good examples are the opcode token
of typically one byte, the prefix token and the immediate tokens which
optionally follow an opcode. Typically RISC machines will have instructions
with one token, and CISC machines will have instructions consisting of
multiple tokens.

To define a token, subclass the :class:`ppci.arch.token.Token` and optionally
add bitfields:

.. testcode:: encoding

    from ppci.arch.token import Token, bit_range

    class Stm8Token(Token):
        class Info:
            size = 8

        opcode = bit_range(0, 8)

In this example an 8-bit token is defined with one field called 'opcode' of
8 bits.


Instruction description
-----------------------

An important part of the backend is the definition of instructions. Every
instruction for a specific machine derives from
:class:`ppci.arch.encoding.Instruction`.


Lets take the nop example of stm8. This instruction can be defined like this:

.. testcode:: encoding

    from ppci.arch.encoding import Instruction, Syntax

    class Nop(Instruction):
        syntax = Syntax(['nop'])
        tokens = [Stm8Token]
        patterns = {'opcode': 0x9d}


Here the nop instruction is defined. It has a syntax of 'nop'.
The syntax is used for creating a nice string
representation of the object, but also during parsing of assembly code.
The tokens contains a list of what tokens this instruction contains.

The patterns attribute contains a list of patterns. In this case
the opcode field is set with the fixed pattern 0x9d.

Instructions are also usable directly, like this:

.. doctest:: encoding

    >>> ins = Nop()
    >>> str(ins)
    'nop'
    >>> ins
    <Nop object at ...>
    >>> type(ins)
    <class 'Nop'>
    >>> ins.encode()
    b'\x9d'

Often, an instruction does not have a fixed syntax. Often an argument
can be specified, for example the stm8 adc instruction:

.. testcode:: encoding

    from ppci.arch.encoding import Operand

    class Stm8ByteToken(Token):
        class Info:
            size = 8

        byte = bit_range(0, 8)

    class AdcByte(Instruction):
        imm = Operand('imm', int)
        syntax = Syntax(['adc', ' ', 'a', ',', ' ', imm])
        tokens = [Stm8Token, Stm8ByteToken]
        patterns = {'opcode': 0xa9, 'byte': imm}

The 'imm' attribute now functions as a variable instruction part. When
constructing the instruction, it must be given:

.. doctest:: encoding

    >>> ins = AdcByte(0x23)
    >>> str(ins)
    'adc a, 35'
    >>> type(ins)
    <class 'AdcByte'>
    >>> ins.encode()
    b'\xa9#'
    >>> ins.imm
    35

As a benefit of specifying syntax and patterns, the default decode classmethod
can be used to create an instruction from bytes:

.. doctest:: encoding
    :options: +ELLIPSIS

    >>> ins = AdcByte.decode(bytes([0xa9,0x10]))
    >>> ins
    <AdcByte object at ...>
    >>> str(ins)
    'adc a, 16'

Another option of constructing instruction classes is adding different
instruction classes to eachother:

.. testcode:: encoding

    from ppci.arch.encoding import Operand

    class Sbc(Instruction):
        syntax = Syntax(['sbc', ' ', 'a'])
        tokens = [Stm8Token]
        patterns = {'opcode': 0xa2}

    class Byte(Instruction):
        imm = Operand('imm', int)
        syntax = Syntax([',', ' ', imm])
        tokens = [Stm8ByteToken]
        patterns = {'byte': imm}

    SbcByte = Sbc + Byte


In the above example, two instruction classes are defined. When combined,
the tokens, syntax and patterns are combined into the last instruction.

.. doctest:: encoding

    >>> ins = SbcByte.decode(bytes([0xa2,0x10]))
    >>> str(ins)
    'sbc a, 16'
    >>> type(ins)
    <class 'ppci.arch.encoding.SbcByte'>


Relocations
-----------

Most instructions can be encoded directly, but some refer to a label
which is not known at the time a single instruction is created. The answer
to this problem is relocation information. When generating instructions
also relocation information is emitted. During link time, or during loading
the relocations are resolved and the instructions are patched.

To define a relocation, subclass :class:`ppci.arch.encoding.Relocation`.

.. testcode:: encoding

    from ppci.arch.encoding import Relocation

    class Stm8WordToken(Token):
        class Info:
            size = 16
            endianness = 'big'

        word = bit_range(0, 16)

    class Stm8Abs16Relocation(Relocation):
        name = 'abs16'
        token = Stm8WordToken
        field = 'word'

        def calc(self, symbol_value, reloc_value):
            return symbol_value


To use this relocation, use it in an instructions 'relocations' function:


.. testcode:: encoding

    class Jp(Instruction):
        label = Operand('label', str)
        syntax = Syntax(['jp', ' ', label])
        tokens = [Stm8Token, Stm8WordToken]
        patterns = {'opcode': 0xcc}

        def relocations(self):
            return [Stm8Abs16Relocation(self.label, offset=1)]

The relocations function returns a list of relocations for this instruction.
In this case it is one relocation entry at offset 1 into the instruction.

Instruction groups
------------------

Instructions often not come alone. They are usually grouped into a set of
instructions, or an instruction set architecture (ISA). An isa can be
created and instructions can be added to it, like this:


.. testcode:: encoding

    from ppci.arch.isa import Isa
    my_isa = Isa()
    my_isa.add_instruction(Nop)


The instructions of an isa can be inspected:

.. doctest:: encoding

    >>> my_isa.instructions
    [<class 'Nop'>]

Instead of adding each instruction manually to an isa, one can also specify
the isa in the class definition of the instruction:


.. testcode:: encoding

    class Stm8Instruction(Instruction):
        isa = my_isa

The class Stm8Instruction and all of its subclasses will now be automatically
added to the isa.

Often there are some common instructions for data definition, such as
the db instruction to define a byte. These are already defined in
data_instructions. Isa's can be added to eachother to combine them, like this:

.. testcode:: encoding

    from ppci.arch.data_instructions import data_isa
    my_complete_isa = my_isa + data_isa


Template matching
-----------------

In order for the compiler to know what instructions must be used when,
use can be made of the built-in pattern matching for instruction selection.
To do this, specify a series of patterns with a possible implementation
for the backend.

.. testcode:: encoding

    @my_isa.pattern('a', 'ADDU8(a, CONSTU8)', size=2, cycles=3, energy=2)
    def pattern_const(context, tree, c0):
        assert reg is A
        value = tree[1].value
        context.emit(AdcByte(value))
        return A

In the function above a function is defined that matches the pattern for
adding a constant to the accumulator (a) register.
The instruction selector will use the
information about size, cycles and energy to determine the best choice
depending on what is given.
If the compiler is run with optimize for size, the size argument will be
weighted heavier in the determination of the choice of pattern.

When a pattern is selected, the function is run, and the corresponding
instruction must be emitted into the context which is given to the function
as a first argument.

See also: :meth:`ppci.arch.isa.Isa.pattern`.

.. note::

    this example uses an accumulator machine, a better example could be
    given using a register machine.


Architecture description
------------------------

Now that we have some instructions defined, it is time to include them
into a target architecture. To create a target architecture, subclass
:class:`ppci.arch.arch.Architecture`.

A subclass must implement a fair amount of member functions. Lets examine
them one by one.

Code generating functions
+++++++++++++++++++++++++

There are several functions that are expected to generate code. Code
can be generated by implementing these functions as generators, but returning
a list of instructions is also possible. All these functions names
start with gen.

These functions are for prologue / epilogue:

* :meth:`ppci.arch.arch.Architecture.gen_prologue`
* :meth:`ppci.arch.arch.Architecture.gen_epilogue`

For creating a call:

* :meth:`ppci.arch.arch.Architecture.gen_call`

During instruction selection phase, the gen_call function is
called to generate code for function calls.

The member functions
:meth:`ppci.arch.arch.Architecture.gen_prologue` and
:meth:`ppci.arch.arch.Architecture.gen_epilogue`
are called at the very
end stage of code generation of a single function.

Architecture information
++++++++++++++++++++++++

Most frontends also need some information, but not all about the target
architecture. For this create architecture info into
:class:`ppci.arch.arch_info.ArchInfo`. This class holds information
about basic type sizes, alignment and endianness of the architecture.

