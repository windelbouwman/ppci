
Testing
=======

Long tests
----------

There are a series of test snippets located in the test/samples folder. If
you want to run these, you can use this:

.. code:: bash

    $ LONGTESTS=all python -m pytest test/

Valid values for the LONGTESTS variable (note that multiple values can be
seperated by comma's):

+-----------------+-------------------------------------------+
| value           | meaning                                   |
+=================+===========================================+
| all             | Go all in, run all tests possible         |
+-----------------+-------------------------------------------+
| any             | Run some extra tests which take           |
|                 | somewhat longer                           |
+-----------------+-------------------------------------------+
| python          | Convert sample snippets to python         |
+-----------------+-------------------------------------------+
| jit             | Run a tricky test in which code is jitted |
+-----------------+-------------------------------------------+
| wasm            | Convert sample snippets to wasm           |
+-----------------+-------------------------------------------+
| riscv,msp430,   | Convert sample snippets to                |
| avr,microblaze, | code for the given architecture           |
| xtensa,arm      |                                           |
+-----------------+-------------------------------------------+

Some targets need iverilog to emulate a certain processor. If you want to run
these, use this:

.. code:: bash

    $ LONGTESTS=all IVERILOG=1 python -m pytest test/

3rd party test suites
---------------------

There exist many different compiler validation suites. Some of them are pure validation sets,
others are part of a compiler toolchain. In order to use these test suites, a series of test
suite adapter files exists.

Available test adapters:

* mcpp (set `MCPP_DIR`) `test/lang/c/test_mcpp_test_suite.py`
* fortran compiler validation system 2.1 (set `FCVS_DIR`) `test/lang/fortran/test_fortran_test_suite.py`

WebAssembly spec
~~~~~~~~~~~~~~~~

The WebAssembly specification contains a validation suite.

To use these tests, clone https://github.com/WebAssembly/spec and set
the environment variable WASM_SPEC_DIR
to the location where the code was cloned.

To run the test spec tests:

.. code:: bash

    $ export WASM_SPEC_DIR=~/GIT/spec
    $ python -m pytest test/wasm/test_suite_full -v

C testsuite
~~~~~~~~~~~

The c-testsuite is a collection of C test cases.

Usage with pytest:

    $ export C_TEST_SUITE_DIR=/path/to/GIT/c-testsuite
    $ python -m pytest test/lang/c/test_c_test_suite.py -v

Usage as a script:

    $ python test_c_test_suite.py /path/to/GIT/c-testsuite

See also:

https://github.com/c-testsuite/c-testsuite

Compiler testing
----------------

There are a number of ways to stress test the compiler.

One way is to compile existing C sourcecode, and see if the code compiles and runs.

Current results:

+---------------+----------+---------+
| test sample   | Compiles | Runs    |
+===============+==========+=========+
| libmad        | yes      | ?       |
+---------------+----------+---------+
| 8cc           | yes      | ?       |
+---------------+----------+---------+
| lcc           | no       | ?       |
+---------------+----------+---------+
| micropython   | no       | ?       |
+---------------+----------+---------+

libmad
~~~~~~

The sourcecode for this test can be found here: https://www.underbit.com/products/mad/

To compile libmad, use the script `tools/compile_libmad.py`. This will compile the libmad sourcecode.

Compilation takes 45 seconds.

8cc
~~~

8cc is a small C compiler which can compile itself. PPCI can also compile it, running it remains a challenge.

Sourcecode is located here: https://github.com/rui314/8cc

To compile 8cc, use the script `tools/compile_8cc.py`

lcc
~~~

lcc is a C compiler written in C. Sourcecode can be found here: https://github.com/drh/lcc

To compile this sourcecode, use the script `tools/compile_lcc.py`

micropython
~~~~~~~~~~~

Micropython is a python implementation for microcontrollers. Website: http://micropython.org/

To compile this sourcecode, use the script `tools/compile_micropython.py`

