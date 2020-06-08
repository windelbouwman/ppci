
Development
===========

This chapter descibes how to develop on ppci.


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

Alternatively a git is also used:

- https://github.com/windelbouwman/ppci


Coding style
------------

All code is intended to be pep8 compliant. You can use the pep8 tool, or run:

.. code:: bash

    $ tox -e flake8

This will check the code for pep8 violations.

On top of this, we use the black formatter to autoformat code.

Future work includes using pylint and mypy for more static code analysis.

Running the testsuite
---------------------

To run the unit tests with the compiler, use `pytest`_:

.. _pytest: https://pytest.org

.. code:: bash

    $ python -m pytest -v test/

Or, yet another way, use tox:

.. code:: bash

    $ tox -e py3

In order to test ppci versus different versions of python, `tox`_ is used. To
run tox, simply run in the root directory:

.. _tox: http://tox.testrun.org

.. code:: bash

    $ tox

Note that those command will **not work properly**:

.. code:: bash

    $ python -m unittest discover -s  # will not recursively discover test cases
    $ python setup.py test  # does not work and is deprecated

:doc:`Read more about testing <testing>`.

Profiling
~~~~~~~~~

If some part is slow, it can be handy to run a profiler. To do this, run
the slow script with the cProfile. The output can be viewed with
pyprof2calltree.

.. code:: bash

    $ python -m cProfile -o profiled.out slow_script.py
    $ pip install pyprof2calltree
    $ pyprof2calltree -i profiled.out -k


Building the docs
-----------------

The docs can be built locally by using `sphinx`_.
Sphinx can be invoked directly:

.. _sphinx: http://www.sphinx-doc.org/en/stable/

.. code:: bash

    $ cd docs
    $ sphinx-build -b html . build

Alternatively the `tox`_ docs environment can be used:

.. code:: bash

    $ tox -e docs

Directory structure
-------------------

- ppci : source code of the ppci library

  - arch : different machine support

    - arm : arm support
    - avr : avr support
    - microblaze
    - mips
    - msp430 : msp430 support
    - riscv
    - stm8
    - x86_64
    - xtensa : xtensa support

  - binutils : assembler and linker
  - cli : command line interface utilities
  - codegen : code generation
  - format : various file formats
  - lang : human readable languages

    - c : c frontend
    - c3 : c3 frontend
    - python : python compilation code
    - tools : language tools

  - opt : IR-code optimization
  - util : utilities

- docs : documentation
- examples : directory with example projects
- test : tests



Continuous integration
----------------------

The compiler is tested for linux:

- https://travis-ci.org/windelbouwman/ppci-mirror

and for windows:

- https://ci.appveyor.com/project/WindelBouwman/ppci-786


Code metrics
------------

Code coverage is reported to the codecov service:

- https://codecov.io/bb/windel/ppci/branch/default

Other code metrics are listed here:

- https://www.openhub.net/p/ppci

- https://libraries.io/pypi/ppci
