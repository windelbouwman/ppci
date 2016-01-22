
Command line tools
==================

This section describes the usage the commandline tools installed with ppci.

.. _ppci-build:

ppci-build.py
-------------

This command can be used to construct :doc:`build files<buildxml>`.

Take for example the stm32f4 blinky project. To build this project,
run ppci-build.py in the project folder:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build.py

Or specify the buildfile a the command line:

.. code:: bash

    $ ppci-build.py -f examples/blinky/build.xml


``--help, -h``

    Display usage help.

``--verbose, -v``

    Increase verbosity of output. Can be given multiple times.

``--buildfile, -f``

    Specify the file to use as build file.


.. _ppci-c3c:

ppci-c3c.py
-----------

Instead of relying on a build system, the :doc:`c3<c3>` compiler can also be
activated stand alone.

.. code:: bash

    $ ppci-c3c.py --machine arm examples/snake/game.c3

``--help, -h``

    Display the usage of the c3 compiler.

``--verbose, -v``

    Increase verbosity of output. Can be given multiple times.


.. _ppci-asm:

ppci-asm.py
-----------

Invoke the assembler.

``sourcefile``

    The sourcefile to assemble.

``--help, -h``

    Display the usage of the assembler.

``--verbose, -v``

    Increase verbosity of output. Can be given multiple times.

``--machine, -m``

    Specify the target machine.

``--output, -o``

    The filename of the output.


.. _ppci-ld:

ppci-ld.py
----------

Linker

``--help, -h``

    Display usage help.

``--verbose, -v``

    Increase verbosity of output. Can be given multiple times.


ppci-objcopy.py
---------------

Objcopy utility to manipulate binary files.

``--help, -h``

    Display usage help.

``--verbose, -v``

    Increase verbosity of output. Can be given multiple times.


ppci-hexutil.py
---------------

Utility to handle hex files.

