
Introduction
============

The ppci (Pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains the following:

- A compiler, an assembler, a linker and a build system
- Language front-ends: Brainfuck, :doc:`c3`
- Backends for various platforms: ARM, Thumb, Python, X86, AVR, MSP430

An example usage of the low level encoding api:

.. doctest::

    >>> from ppci.arch.x86_64 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['

An other example:

.. doctest::

    >>> import io
    >>> from ppci.api import asm
    >>> source_file = io.StringIO("""section code
    ... mov rax, 60
    ... mov rdi, 42""")
    >>> obj = asm(source_file, 'x86_64')
    >>> obj.get_section('code').data
    bytearray(b'H\xb8<\x00\x00\x00\x00\x00\x00\x00H\xbf*\x00\x00\x00\x00\x00\x00\x00')
