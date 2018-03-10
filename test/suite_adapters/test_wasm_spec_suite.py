
"""

Run the tests as can be found here

https://github.com/WebAssembly/spec/tree/master/test

The directory structure of this spec is as follows:

- test
  - core
    - address.wast  -> test snippet in wasm text format with additional test info

To use these tests, clone https://github.com/WebAssembly/spec and set the environment variable WASM_SPEC_DIR
to the location where the code was cloned.
"""

# TODO: this is a placeholder for the web assembly spec test suite

# COOL IDEA: use python-requests to download the suite on demand to some temporary folder!


import unittest
import glob
import os.path
import io

from ppci.wasm import read_wat
from ppci.common import CompilerError


def create_test_function(cls, filename):
    """ Create a test function for a single snippet """
    core_test_directory, snippet_filename = os.path.split(filename)
    test_function_name = 'test_' + snippet_filename.replace('.', '_').replace('-', '_')

    def test_function(self):
        output_file = io.StringIO()
        with open(filename, 'r') as f:
            module = read_wat(f)

        # TODO: check output for correct values:
        print(output_file.getvalue())

    if hasattr(cls, test_function_name):
        raise ValueError('Duplicate test case {}'.format(test_function_name))
    setattr(cls, test_function_name, test_function)


def wasm_spec_populate(cls):
    """ Decorator function which can populate a unittest.TestCase class """
    if 'WASM_SPEC_DIR' in os.environ:
        wasm_spec_directory = os.path.normpath(os.environ['WASM_SPEC_DIR'])
        core_test_directory = os.path.join(wasm_spec_directory, 'test', 'core')
        for filename in sorted(glob.iglob(os.path.join(core_test_directory, '*.wast'))):
            create_test_function(cls, filename)
    return cls


@wasm_spec_populate
class WasmSpecTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main(verbosity=2)