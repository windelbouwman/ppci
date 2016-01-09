
Introduction
============

The ppci (Pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains the following:

- A compiler, an assembler, a linker and a build system
- Language front-ends: Brainfuck, :doc:`c3`
- Backends for various platforms: ARM, Thumb, Python, X86, AVR, MSP430

An example usage of the low level encoding api:

.. code-block:: python

    >>> from ppci.target.x86 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['
