""" Unit test adapter for c-testsuite

The c-testsuite is a collection of C test cases.

This is an adapter script to enable running of those snippets
as unittests.

Usage with pytest:

    $ export C_TEST_SUITE_DIR=/path/to/GIT/c-testsuite
    $ python -m pytest test_c_test_suite.py -v

Usage as a script:

    $ python test_c_test_suite.py /path/to/GIT/c-testsuite

See also:

https://github.com/c-testsuite/c-testsuite

"""


import unittest
import glob
import argparse
import os
import logging

from ppci.common import CompilerError, logformat
from ppci import api
from ppci.lang.c import COptions

this_dir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("c-test-suite")


def c_test_suite_populate(cls):
    """ Enrich a unittest.TestCase with a function for each test snippet. """
    if "C_TEST_SUITE_DIR" in os.environ:
        c_test_suite_directory = os.path.normpath(
            os.environ["C_TEST_SUITE_DIR"]
        )

        for filename in get_test_snippets(c_test_suite_directory):
            create_test_function(cls, filename)
    else:

        def test_stub(self):
            self.skipTest(
                "Please specify C_TEST_SUITE_DIR for the C test suite"
            )

        setattr(cls, "test_stub", test_stub)
    return cls


def get_test_snippets(c_test_suite_directory):
    snippet_folder = os.path.join(
        c_test_suite_directory, "tests", "single-exec"
    )

    # Check if we have a folder:
    if not os.path.isdir(snippet_folder):
        raise ValueError("{} is not a directory".format(snippet_folder))

    for filename in sorted(glob.iglob(os.path.join(snippet_folder, "*.c"))):

        yield filename


def create_test_function(cls, filename):
    """ Create a test function for a single snippet """
    snippet_filename = os.path.split(filename)[1]
    test_name = os.path.splitext(snippet_filename)[0]
    test_name = test_name.replace(".", "_").replace("-", "_")
    test_function_name = "test_" + test_name

    def test_function(self):
        perform_test(filename)

    if hasattr(cls, test_function_name):
        raise ValueError("Duplicate test case {}".format(test_function_name))
    setattr(cls, test_function_name, test_function)


def perform_test(filename):
    """ Try to compile the given snippet. """
    logger.info("Step 1: Compile %s!", filename)
    march = "x86_64"
    coptions = COptions()
    libc_include = os.path.join(this_dir, "..", "..", "..", "librt", "libc")
    coptions.add_include_path(libc_include)
    coptions.enable('freestanding')
    with open(filename, "r") as f:
        try:
            obj = api.cc(f, march, coptions=coptions)
        except CompilerError as ex:
            ex.print()
            raise
    logger.info("Compilation complete, %s", obj)

    logger.info("Step 2: Run it!")
    logger.error("Running not yet implemented")
    # TODO


@c_test_suite_populate
class CTestSuiteTestCase(unittest.TestCase):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument(
        "folder", help="the folder with the c test suite.",
    )
    args = parser.parse_args()

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)

    for filename in get_test_snippets(args.folder):
        perform_test(filename)

    print("OK.")
