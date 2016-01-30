

Introduction
============

The ppci (pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains the following:

- A Compiler, an assembler, a linker and a build system
- Language front-ends: Brainfuck, c3
- Backends: 6500, arm, avr, msp430, risc-v, x86_64

.. warning::

    **This project is in alpha state and not ready for production use!**

Command line tools
------------------

Use it to build projects:

.. code:: bash

    $ pip install ppci
    $ ppci-build.py -f examples/build.xml
    $ qemu-system-arm -M lm3s6965evb -kernel snake.bin -serial stdio

This runs the snake demo on an emulated (qemu) lm3s demo board and displays
the game to the console.

Api
---

Or use the api:

.. code-block:: python

    >>> from ppci.arch.x86_64 import instructions, registers
    >>> i = instructions.Pop(registers.rbx)
    >>> i.encode()
    b'['

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

Documentation
-------------

Documentation can be found here:

- http://ppci.readthedocs.org/


|dronestate|_
|appveyor|_
|codecov|_
|docstate|_
|version|_
|devstate|_
|pyimpls|_
|pyversions|_
|license|_
|downloads|_


.. |codecov| image:: https://codecov.io/bitbucket/windel/ppci/coverage.svg?branch=default
.. _codecov: https://codecov.io/bitbucket/windel/ppci?branch=default


.. |downloads| image:: https://img.shields.io/pypi/dm/ppci.png
.. _downloads: https://pypi.python.org/pypi/ppci


.. |version| image:: https://img.shields.io/pypi/v/ppci.png
.. _version: https://pypi.python.org/pypi/ppci


.. |license| image:: https://img.shields.io/pypi/l/ppci.png
.. _license: https://pypi.python.org/pypi/ppci


.. |devstate| image:: https://img.shields.io/pypi/status/ppci.png
.. _devstate: https://pypi.python.org/pypi/ppci


.. |pyversions| image:: https://img.shields.io/pypi/pyversions/ppci.png
.. _pyversions: https://pypi.python.org/pypi/ppci


.. |pyimpls| image:: https://img.shields.io/pypi/implementation/ppci.png
.. _pyimpls: https://pypi.python.org/pypi/ppci


.. |dronestate| image:: https://drone.io/bitbucket.org/windel/ppci/status.png
.. _dronestate: https://drone.io/bitbucket.org/windel/ppci


.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/h0h5huliflrac65o?svg=true
.. _appveyor: https://ci.appveyor.com/project/WindelBouwman/ppci-786


.. |docstate| image:: https://readthedocs.org/projects/ppci/badge/?version=latest
.. _docstate: https://ppci.readthedocs.org/en/latest
