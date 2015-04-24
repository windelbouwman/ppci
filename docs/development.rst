
Development
===========

This chapter descibes how to develop on ppci.

Communication
-------------

Join the #ppci irc channel on freenode!


Running the testsuite
---------------------

To run the unit tests with the compiler, use pytest:

.. code:: bash

    $ pytest -v test/

Or use the unittest module:

.. code:: bash

    $ python -m unittest discover -s test

In order to test ppci versus different versions of python, tox is used. To
run tox, simply run in the root directory:

.. code:: bash

    $ tox


Building the docs
-----------------
The docs can be build locally by using sphinx. Make sure that ppci is on your
PYTHONPATH

.. code:: bash

    $ export PYTHONPATH=your_ppci_root
    $ cd docs
    $ sphinx-build -b html . build

Alternatively the tox docs environment can be used:

.. code:: bash

    $ tox -e docs
