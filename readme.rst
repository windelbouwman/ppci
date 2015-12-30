

Introduction
============

The ppci (Pure python compiler infrastructure) project is a compiler
written entirely in python.

The project contains the following:

- Language front-ends: Brainfuck, c3
- Various code optimizers
- Backends for various platforms: ARM, Thumb, Python, X86, AVR
- Assembler
- Linker
- Build system

**Warning: This project is in alpha state and not ready for production use!**

Quick guide
-----------

ppci can be installed using pip:

.. code:: bash

    $ pip install ppci

To invoke the builder and compile the snake demo, use the following:

.. code:: bash

    $ ppci-build.py -f examples/build.xml

If the compilation was succesful, the snake demo compiled into
'examples/snake.bin'. This is a binary file with ARM-code which can be run
in qemu as follows:

.. code:: bash

    $ qemu-system-arm -M lm3s6965evb -kernel snake.bin -serial stdio

This runs the snake demo on an emulated lm3s demo board and displays
the game to the console.


Instead of using the command line tools, you can also
use the api.

Links
-----

Sourcecode is located here:

- https://bitbucket.org/windel/ppci
- https://pikacode.com/windel/ppci/


Documentation can be found here:

- http://ppci.rtfd.org/


|dronestate|_
|appveyor|_
|codecov|_
|devstate|_
|docstate|_
|version|_
|pyimpls|_
|pyversions|_
|license|_
|downloads|_

openhub_

.. |codecov| image:: https://codecov.io/bitbucket/windel/ppci/coverage.svg?branch=default
.. _codecov: https://codecov.io/bitbucket/windel/ppci?branch=default

.. _openhub: https://www.openhub.net/p/ppci

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
.. _docstate: https://ppci.rtfd.org/en/latest
