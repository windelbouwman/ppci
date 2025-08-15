#!/usr/bin/env python

"""MCPP validation suite runner.

See homepage: http://mcpp.sourceforge.net

This script helps to run the MCPP preprocessor validation suite.

The validation suite is organized into directories test-t, test-c and test-l.
Test snippets are prefixed with n_ for valid snippets, i_ prefixed snippets
contain implementation defined snippets, e_ indicates that this file will
result in an error.

The test-t directory contains .t files which are text files to be preprocessed.
The test-c directory contains .c files which are the same as the .t files
but are valid c programs which might be compiled.

See also tools/mcpp/mcpp_validation.py

"""

import unittest
import glob
import os.path
import io

from ppci.api import preprocess
from ppci.lang.c import COptions

this_dir = os.path.dirname(os.path.abspath(__file__))


def create_test_function(cls, filename):
    """Create a test function for a single snippet"""
    test_t_directory, snippet_filename = os.path.split(filename)
    test_function_name = "test_" + snippet_filename.replace(".", "_")

    def test_function(self):
        coptions = COptions()
        coptions.enable("trigraphs")
        coptions.add_include_path(test_t_directory)
        libc_dir = os.path.join(this_dir, "..", "..", "..", "librt", "libc")
        coptions.add_include_path(libc_dir)

        output_file = io.StringIO()
        with open(filename) as f:
            preprocess(f, output_file, coptions)
        # TODO: check output for correct values:
        print(output_file.getvalue())

    if hasattr(cls, test_function_name):
        raise ValueError(f"Duplicate test {test_function_name}")

    setattr(cls, test_function_name, test_function)


def mcpp_populate(cls):
    if "MCPP_DIR" in os.environ:
        mcpp_directory = os.path.normpath(os.environ["MCPP_DIR"])
        test_t_directory = os.path.join(mcpp_directory, "test-t")
        files = sorted(glob.iglob(os.path.join(test_t_directory, "n_*.t")))
        black_list = [
            "n_token.t",  # contains C++ token '::'
            "n_cnvucn.t",  # contains chinese chars # TODO
            "n_ucn1.t",  # non utf8 chars # TODO
            "n_3_4.t",  # raises an error on purpose.
            "n_8.t",  # raises error as an example
        ]
        for fullfile in files:
            filename = os.path.split(fullfile)[1]
            if filename in black_list:
                continue
            create_test_function(cls, fullfile)
    else:

        def test_func(self):
            self.skipTest(
                "Please specify MCPP_DIR if you wish to run the mcpp tests."
                "For example: export MCPP_DIR=~/SVN/mcpp-code"
            )

        setattr(cls, "test_stub", test_func)
    return cls


@mcpp_populate
class McppTestCase(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
