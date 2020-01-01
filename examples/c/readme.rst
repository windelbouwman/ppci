
C sample programs
=================

This directory contains some snippets of C source code. Try to compile them
with ppci:

.. code:: bash

    $ ppci-cc -c sample1.c

or with gcc:

.. code:: bash

    $ gcc -c sample1.c


You can also dump a syntax tree with pycparsing or the ppci cparser:

.. code:: bash

    $ python demo_pycparser.py sample1.c
