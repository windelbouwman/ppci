
.. _commandline:

Command line tools
==================

This section describes the usage the commandline tools installed with ppci.

Take for example the stm32f4 blinky project. To build this project,
run ppci-build.py in the project folder:

.. code:: bash

    $ cd examples/blinky
    $ ppci-build

This command is used to construct :doc:`build files<buildxml>`.

Or specify the buildfile a the command line:

.. code:: bash

    $ ppci-build -f examples/blinky/build.xml

Instead of relying on a build system, the :doc:`c3<lang/c3>` compiler can also be
activated stand alone.

.. code:: bash

    $ ppci-c3c --machine arm examples/snake/game.c3

.. _ppci-c3c:
.. autoprogram:: ppci.cli.c3c:parser
    :prog: ppci-c3c

.. _ppci-build:
.. autoprogram:: ppci.cli.build:parser
    :prog: ppci-build

.. _ppci-asm:
.. autoprogram:: ppci.cli.asm:parser
    :prog: ppci-asm

.. _ppci-ld:
.. autoprogram:: ppci.cli.link:parser
    :prog: ppci-ld

.. autoprogram:: ppci.cli.objcopy:parser
    :prog: ppci-objcopy

.. autoprogram:: ppci.cli.objdump:parser
    :prog: ppci-objdump

.. _ppci-opt:
.. autoprogram:: ppci.cli.opt:parser
    :prog: ppci-opt

.. _ppci-cc:
.. autoprogram:: ppci.cli.cc:parser
    :prog: ppci-cc

.. autoprogram:: ppci.cli.pascal:parser
    :prog: ppci-pascal

.. autoprogram:: ppci.cli.pycompile:parser
    :prog: ppci-pycompile

.. autoprogram:: ppci.cli.readelf:parser
    :prog: ppci-readelf

.. autoprogram:: ppci.cli.wasmcompile:parser
    :prog: ppci-wasmcompile

.. autoprogram:: ppci.cli.yacc:parser
    :prog: ppci-yacc

.. autoprogram:: ppci.cli.wasm2wat:parser
    :prog: ppci-wasm2wat

.. autoprogram:: ppci.cli.wat2wasm:parser
    :prog: ppci-wat2wasm

.. autoprogram:: ppci.cli.wabt:parser
    :prog: ppci-wabt
