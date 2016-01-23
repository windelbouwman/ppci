
Introduction
============

The ppci (pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains:

- A :ref:`compiler<ppci-c3c>`, an :ref:`assembler<ppci-asm>`,
  a :ref:`linker<ppci-ld>` and a :ref:`build system<ppci-build>`
- Language front-ends: Brainfuck, :doc:`c3<c3>`
- Backends for various platforms: :ref:`arm`, :ref:`avr`, :ref:`msp430`,
  python, thumb,
  :ref:`x86_64`

An example usage of the low level encoding :doc:`api<api>`:

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

.. warning::
    This project is in alpha state and not ready for production use!
