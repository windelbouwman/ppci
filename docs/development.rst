
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

Alternatively a git mirror is also created:

- https://github.com/windelbouwman/ppci-mirror


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

Or use the unittest module:

.. code:: bash

    $ python -m unittest discover -s test

Or, yet another way, use tox:

.. code:: bash

    $ tox -e py3

In order to test ppci versus different versions of python, `tox`_ is used. To
run tox, simply run in the root directory:

.. _tox: http://tox.testrun.org

.. code:: bash

    $ tox

Long tests
~~~~~~~~~~

There are a series of test snippets located in the test/samples folder. If
you want to run these, you can use this:

.. code:: bash

    $ LONGTESTS=1 python -m pytest test/

Some targets need iverilog to emulate a certain processor. If you want to run
these, use this:

.. code:: bash

    $ LONGTESTS=1 IVERILOG=1 python -m pytest test/

Profiling
~~~~~~~~~

If some part is slow, it can be handy to run a profiler. To do this, run
the slow script with the cProfile. The output can be viewed with
pyprof2calltree.

.. code:: bash

    $ python -m cProfile -o profiled.out slow_script.py
    $ pip install pyprof2calltree
    $ pyprof2calltree -i profiled.out -k

Debugging tests
~~~~~~~~~~~~~~~

To debug test cases, a handy trick is to use pudb (when not using fancy ide
like vscode or pycharm). To do this, specify the debugger to use with pytest
like this:

.. code:: bash

    $ pytest -v --pdb --pdbcls pudb.debugger:Debugger --capture=no

Debugging dynamic code
~~~~~~~~~~~~~~~~~~~~~~

Sometimes, the python interpreter might crash due to playing with dynamically
injected code. To debug this, we can use gdb for example.

.. code:: bash

    $ gdb --args python script.py
    (gdb) run

Once the program crashes, one can disassemble and print info:

.. code:: bash

    (gdb) bt
    (gdb) disassemble /r 0x7fff000, 0x7fff200
    (gdb) info registers

Debugging python code
~~~~~~~~~~~~~~~~~~~~~

Alternatively, when facing a python exception, one might want to try the pudb
debugger like this:

.. code:: bash

    python -m pudb crashing_script.py

3rd party test suites
~~~~~~~~~~~~~~~~~~~~~

There exist many different compiler validation suites. Some of them are pure validation sets,
others are part of a compiler toolchain. In order to use these test suites, a series of test
suite adapter files exists.

Available test adapters:

* mcpp (set `MCPP_DIR`) `test/lang/c/test_mcpp_test_suite.py`
* wasm spec (set `WASM_SPEC_DIR`) `test/wasm/test_suite_full.py`
* fortran compiler validation system 2.1 (set `FCVS_DIR`) `test/lang/fortran/test_fortran_test_suite.py`

To run for example wasm test spec tests:

.. code:: bash

    $ WASM_SPEC_DIR=~/GIT/spec python -m pytest test/wasm/test_suite_full -v

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


Release procedure
-----------------

This is more a note to self section on how to create a new release.

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
#. Update docs/changelog.rst

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
