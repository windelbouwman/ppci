
Introduction
============

The ppci (pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains the following:

- A Compiler, an assembler, a linker and a build system
- Language front-ends: Brainfuck, c3
- Backends: 6500, arm, avr, msp430, risc-v, stm8, x86_64

.. warning::

    **This project is in alpha state and not ready for production use!**

Api
---

Api example to compile c3 code:

.. code-block:: python

    >>> import io
    >>> from ppci.api import c3c, link
    >>> source_file = io.StringIO("""
    ... module main;
    ... function void print(string txt) {
    ... }
    ... function void main() {
    ...  print("Hello world");
    ... }""")
    >>> obj = c3c([source_file], [], 'arm')
    >>> obj = link([obj])

Example how to assemble some assembly code:

.. code-block:: python

    >>> import io
    >>> from ppci.api import asm
    >>> source_file = io.StringIO("""section code
    ... pop rbx
    ... push r10
    ... mov rdi, 42""")
    >>> obj = asm(source_file, 'x86_64')
    >>> obj.get_section('code').data
    bytearray(b'[ARH\xbf*\x00\x00\x00\x00\x00\x00\x00')

Example of the low level api usage:

.. code-block:: python

    >>> from ppci.arch.x86_64 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['

Documentation
-------------

Documentation can be found here:

- https://ppci.readthedocs.io/


|dronestate|_
|appveyor|_
|codecov|_
|docstate|_


.. |codecov| image:: https://codecov.io/bb/windel/ppci/branch/default/graph/badge.svg
.. _codecov: https://codecov.io/bb/windel/ppci/branch/default


.. |dronestate| image:: https://drone.io/bitbucket.org/windel/ppci/status.png
.. _dronestate: https://drone.io/bitbucket.org/windel/ppci


.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/h0h5huliflrac65o?svg=true
.. _appveyor: https://ci.appveyor.com/project/WindelBouwman/ppci-786


.. |docstate| image:: https://readthedocs.org/projects/ppci/badge/?version=latest
.. _docstate: https://ppci.readthedocs.io/en/latest
