
Command line tools
==================

This section describes the usage of some commandline tools installed with ppci.


ppci-build.py
-------------

This command can be used to construct build files (see :doc:`buildxml`).

Take for example the stm32f4 led project build file:

.. literalinclude:: ../test/data/stm32f4xx/build.xml
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

Instead of relying on a build system, the c3 compiler can also be activated
stand alone.

.. code:: bash

    $ ppci-c3c.py --target arm examples/snake/game.c3

ppci-asm.py
-----------

Invoke the assembler.
