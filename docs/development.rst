
Development
===========

This chapter descibes how to develop on ppci.

Communication
-------------

Join the #ppci irc channel on freenode!

Source code
-----------

The sourcecode of the project is located at these repositories:

- https://bitbucket.org/windel/ppci
- https://pikacode.com/windel/ppci/

To check out the latest code and work use the development version use these
commands to checkout the source code and setup ppci such that you can use it
without having to setup your python path.

.. code:: bash

    $ mkdir HG
    $ cd HG
    $ hg clone https://bitbucket.org/windel/ppci
    $ cd ppci
    $ sudo python setup.py develop


Continuous integration
----------------------

The compiler is tested for linux:

- https://drone.io/bitbucket.org/windel/ppci


and for windows:

- https://ci.appveyor.com/project/WindelBouwman/ppci-786


Code metrics
------------

Code coverage is reported to the codecov service:

- https://codecov.io/bitbucket/windel/ppci?branch=default

Other code metrics are listed at openhub:

- https://www.openhub.net/p/ppci


Running the testsuite
---------------------

To run the unit tests with the compiler, use pytest:

.. code:: bash

    $ python -m pytest -v test/

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


Release procedure
-----------------

Make sure all tests pass before a release.

Package and upload the python package with:

.. code:: bash

    $ hg update release
    $ hg merge default
    # Check version number
    $ tox
    $ hg tag x.y.z
    $ hg update x.y.z
    $ python setup.py sdist upload
    $ hg update default
    $ hg merge release

Increase the version number.
