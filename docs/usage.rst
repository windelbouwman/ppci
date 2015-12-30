
Command line tools
==================

This section describes the usage the commandline tools installed with ppci.

.. _ppci-build:

ppci-build.py
-------------

This command can be used to construct build files (see :doc:`buildxml`).

Take for example the stm32f4 led project build file:

.. literalinclude:: ../examples/blinky/build.xml
    :language: xml
    :linenos:


To build this project, run ppci-build.py in the same directory:

.. code:: bash

    $ cd test/data/stm32f4xx
    $ ppci-build.py

Or specify the buildfile:

.. code:: bash

    $ ppci-build.py -f test/data/stm32f4xx/build.xml


ppci-c3c.py
-----------

Instead of relying on a build system, the :doc:`c3` compiler can also be
activated stand alone.

.. code:: bash

    $ ppci-c3c.py --target arm examples/snake/game.c3

ppci-asm.py
-----------

Invoke the assembler.

ppci-objcopy.py
---------------

Objcopy utility to manipulate binary files.


ppci-hexutil.py
---------------

Utility to handle hex files.

