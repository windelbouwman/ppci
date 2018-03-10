
# Suite adapters

This directory contains adapters to test suites of other projects.
The idea is to create unittest.TestCase classes dynamically and
create test cases for each test case in the 3rd party test suite.
This way the tests can be run by pytest.

## mcpp

mcpp is a preprocessor project which contains
a good test suite for C preprocessors.

Set the `MCPP_DIR` environment variable to folder of mcpp to
enable this test suite.

## gcc

the GCC compiler contains a lot of test snippets.

TODO: Figure out how these tests are organized

## LLVM

TODO: For sure there are useful tests that could be re-used.

## WASM

TODO: the web assembly spec contains a suite of tests which can be run

Set the `WASM_SPEC_DIR` environment variable to enable loading of this
suite.

## Fortran

There exists a fortran test suite collection "fortran compiler
validation system" (fcvs21.tar.Z).

For fortran, set the `FCVS_DIR` environment variable to the directory
where the fortran compiler validation system (fcvs21.tar.Z) files are located.