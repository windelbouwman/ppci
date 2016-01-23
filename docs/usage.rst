
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
.. autoprogram:: ppci.commands:c3c_parser
    :prog: ppci-c3c.py

.. _ppci-build:
.. autoprogram:: ppci.commands:build_parser
    :prog: ppci-build.py

.. _ppci-asm:
.. autoprogram:: ppci.commands:asm_parser
    :prog: ppci-asm.py

.. _ppci-ld:
.. autoprogram:: ppci.commands:link_parser
    :prog: ppci-ld.py

.. autoprogram:: ppci.commands:objcopy_parser
    :prog: ppci-objcopy.py

.. autoprogram:: ppci.commands:objdump_parser
    :prog: ppci-objdump.py

.. autoprogram:: ppci.commands:hexutil_parser
    :prog: ppci-hexutil.py
