
Introduction
============

The ppci (pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains:

- A set of :ref:`command line utilities<commandline>`, such as ppci-cc and ppci-ld.
- A :ref:`pythonic api<api>`
- Language front-ends:
    - :doc:`C<reference/lang/c>`
    - :doc:`Python<reference/lang/python>`
    - :doc:`Brainfuck<reference/lang/bf>`
    - :doc:`Pascal<reference/lang/pascal>`
    - :doc:`c3<reference/lang/c3>`
    - :doc:`Fortran<reference/lang/fortran>`
    - :doc:`Basic<reference/lang/basic>`
- Backends for various target architectures:
    - :ref:`6500<mcs6500>`, :ref:`arm`, :ref:`avr`, :ref:`m68k`, :ref:`microblaze`
    - :ref:`msp430`, :ref:`or1k`, :ref:`ricv-v<riscv>`, :ref:`stm8`
    - :ref:`x86_64`, :ref:`xtensa`
- Support for:
    - :ref:`WebAssembly<wasm>`
    - :ref:`java JVM<jvm>`
    - :ref:`OCaml bytecode<ocaml>`
- Support for various file formats:
    - :ref:`hexfile<hexfile>`
    - :ref:`s-records<srecord>`
    - :ref:`ELF files<elf>`
    - :ref:`exe files<exe>`
- A simple :ref:`intermediate language<ir>`
- Machine independent :ref:`code generation algorithms<codegen>`
  for register allocation and instruction selection
- A simple way to :ref:`describe an instruction set<encoding>`

An example of :ref:`command-line<commandline>` usage:

.. code:: bash

    $ cd examples/linux64/hello-make
    $ ppci-cc -c -O1 -o hello.o hello.c
    ...
    $ ppci-ld --entry main --layout linux64.ld hello.o -o hello
    ...
    $ ./hello
    Hello, World!

An example usage of the :doc:`library API<reference/api>`:

.. doctest::

    >>> import io
    >>> from ppci.api import cc, link
    >>> source_file = io.StringIO("""
    ...  int printf(char* fmt) { }
    ...  
    ...  void main() {
    ...     printf("Hello world!\n");
    ...  }
    ... """)
    >>> obj = cc(source_file, 'arm')
    >>> obj = link([obj])

Moving to the assembly level:

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

Or even lower level:

.. doctest::

    >>> from ppci.arch.x86_64 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['

.. warning::
    This project is in alpha state and not ready for production use!
