
Development
===========

This chapter descibes how to develop on ppci.


Communication
-------------

Join the #ppci irc channel on freenode!

Or visit the forum:

- https://groups.google.com/d/forum/ppci-dev

Source code
-----------

The sourcecode repository of the project is located at these locations:

- https://bitbucket.org/windel/ppci
- https://pikacode.com/windel/ppci/
- https://mercurial.tuxfamily.org/ppci/ppci

To check out the latest code and work use the development version use these
commands to checkout the source code and setup ppci such that you can use it
without having to setup your python path.

.. code:: bash

    $ mkdir HG
    $ cd HG
    $ hg clone https://bitbucket.org/windel/ppci
    $ cd ppci
    $ sudo python setup.py develop


Running the testsuite
---------------------

To run the unit tests with the compiler, use `pytest`_:

.. _pytest: https://pytest.org

.. code:: bash

    $ python -m pytest -v test/

Or use the unittest module:

.. code:: bash

    $ python -m unittest discover -s test

In order to test ppci versus different versions of python, `tox`_ is used. To
run tox, simply run in the root directory:

.. _tox: http://tox.testrun.org

.. code:: bash

    $ tox

Building the docs
-----------------

The docs can be build locally by using `sphinx`_.
Sphinx can be invoked directly:

.. _sphinx: http://www.sphinx-doc.org/en/stable/

.. code:: bash

    $ cd docs
    $ sphinx-build -b html . build

Alternatively the `tox`_ docs environment can be used:

.. code:: bash

    $ tox -e docs


Release procedure
-----------------

#. Determine the version numbers of this release and the next.
#. Switch to the release branch and merge the default branch into the
   release branch.

    .. code:: bash

        $ hg update release
        $ hg merge default
        $ hg commit

#. Check the version number in ppci/__init__.py
#. Make sure all tests pass and fix them if not.

    .. code:: bash

        $ tox

#. Tag this release with the intended version number and update to this tag.

    .. code:: bash

        $ hg tag x.y.z
        $ hg update x.y.z

#. Package and upload the python package. The following command creates a
   tar gz archive as well as a wheel package.

    .. code:: bash

        $ python setup.py sdist bdist_wheel upload

#. Switch back to the default branch and merge the release branch into the
   default branch.

    .. code:: bash

        $ hg update default
        $ hg merge release
        $ hg commit

#. Increase the version number in ppci/__init__.py.

Continuous integration
----------------------

The compiler is tested for linux:

- https://drone.io/bitbucket.org/windel/ppci


and for windows:

- https://ci.appveyor.com/project/WindelBouwman/ppci-786


Code metrics
------------

Code coverage is reported to the codecov service:

- https://codecov.io/bb/windel/ppci/branch/default

Other code metrics are listed here:

- https://www.openhub.net/p/ppci

- https://libraries.io/pypi/ppci
