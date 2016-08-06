
Introduction
============

The ppci (pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains:

- A :ref:`compiler<ppci-c3c>`, an :ref:`assembler<ppci-asm>`,
  a :ref:`linker<ppci-ld>` and a :ref:`build system<ppci-build>`
- Language front-ends: Brainfuck, :doc:`c3<c3>`
- Backends:  :ref:`6500<mos6500>`, :ref:`arm`,
  :ref:`avr`,
  :ref:`msp430`, :ref:`ricv-v<riscv>`, :ref:`x86_64`

An example usage of the low level encoding :doc:`api<api>`:

.. doctest::

    >>> from ppci.arch.x86_64 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['

Another example:

.. doctest::

    >>> import io
    >>> from ppci.api import asm
    >>> source_file = io.StringIO("""section code
    ... pop rbx
    ... push r10
    ... mov rdi, 42""")
    >>> obj = asm(source_file, 'x86_64')
    >>> obj.get_section('code').data
    bytearray(b'[ARH\xbf*\x00\x00\x00\x00\x00\x00\x00')

And yet another example:

.. doctest::

    >>> import io
    >>> from ppci.api import c3c, link
    >>> source_file = io.StringIO("""
    ...  module main;
    ...  function void print(string txt) { }
    ...  function void main() { print("Hello world"); }
    ... """)
    >>> obj = c3c([source_file], [], 'arm')
    >>> obj = link([obj])

.. warning::
    This project is in alpha state and not ready for production use!
