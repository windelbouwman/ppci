
.. _commandline:

Command line tools
==================

This section describes the usage the commandline tools installed with ppci.

Take for example the stm32f4 blinky project. To build this project,
run ppci-build.py in the project folder:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build.py

This command is used to construct :doc:`build files<buildxml>`.

Or specify the buildfile a the command line:

.. code:: bash

    $ ppci-build.py -f examples/blinky/build.xml

Instead of relying on a build system, the :doc:`c3<c3>` compiler can also be
activated stand alone.

.. code:: bash

    $ ppci-c3c.py --machine arm examples/snake/game.c3

.. _ppci-c3c:
.. autoprogram:: ppci.cli.c3c:parser
    :prog: ppci-c3c.py

.. _ppci-build:
.. autoprogram:: ppci.cli.build:parser
    :prog: ppci-build.py

.. _ppci-asm:
.. autoprogram:: ppci.cli.asm:parser
    :prog: ppci-asm.py

.. _ppci-ld:
.. autoprogram:: ppci.cli.link:parser
    :prog: ppci-ld.py

.. autoprogram:: ppci.cli.objcopy:parser
    :prog: ppci-objcopy.py

.. autoprogram:: ppci.cli.objdump:parser
    :prog: ppci-objdump.py

.. autoprogram:: ppci.cli.opt:parser
    :prog: ppci-opt.py

.. autoprogram:: ppci.cli.cc:parser
    :prog: ppci-cc.py

.. autoprogram:: ppci.cli.pascal:parser
    :prog: ppci-pascal.py

.. autoprogram:: ppci.cli.pycompile:parser
    :prog: ppci-pycompile.py

.. autoprogram:: ppci.cli.wasmcompile:parser
    :prog: ppci-wasmcompile.py
