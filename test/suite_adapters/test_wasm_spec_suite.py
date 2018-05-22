
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

from ppci.wasm import read_wat, Module
from ppci.common import CompilerError
from ppci.lang.sexpr import parse_sexpr, parse_multiple_sexpr


def perform_test(filename):
    # if not os.path.basename(filename).startswith('z'):
    #     return
    print(filename)
    with open(filename, 'rt', encoding='utf-8') as f:
        source_text = f.read()

    try:
        output_file = io.StringIO()
        s_expressions = parse_multiple_sexpr(source_text)
        for s_expr in s_expressions:
            # print(s_expr)
            if s_expr[0] == 'module':
                if 'binary' in s_expr:
                    # We have (module binary "")
                    # We can pass this to the binary reading
                    pass
                else:
                    m1 = Module(s_expr)
                    # todo: next step:
                    # m2 = Module(m1.to_string())
                    # assert m1.to_bytes() == m2.to_bytes()
                    
            else:
                # print('Unknown directive', s_expr[0])
                pass

        # TODO: check output for correct values:
        print(output_file.getvalue())
    except CompilerError as ex:
        print('Exception:', ex)
        lines = list(io.StringIO(source_text))
        ex.render(lines)
        raise


def create_test_function(cls, filename):
    """ Create a test function for a single snippet """
    core_test_directory, snippet_filename = os.path.split(filename)
    test_function_name = 'test_' + os.path.splitext(snippet_filename)[0].replace('.', '_').replace('-', '_')

    def test_function(self):
        perform_test(filename)

    if hasattr(cls, test_function_name):
        raise ValueError('Duplicate test case {}'.format(test_function_name))
    setattr(cls, test_function_name, test_function)


def wasm_spec_populate(cls):
    """ Decorator function which can populate a unittest.TestCase class """
    if 'WASM_SPEC_DIR' in os.environ:
        wasm_spec_directory = os.path.normpath(os.environ['WASM_SPEC_DIR'])
        core_test_directory = os.path.join(wasm_spec_directory, 'test', 'core')
        assert os.path.isdir(core_test_directory), "WASM_SPEC_DIR is set, but not valid"
        for filename in sorted(glob.iglob(os.path.join(core_test_directory, '*.wast'))):
            create_test_function(cls, filename)
    return cls


@wasm_spec_populate
class WasmSpecTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    # Three ways to run this:
    
    # unittest.main(verbosity=2)
    
    # perform_test(r'C:\dev\wasm\spec\test\core\br_table.wast')
    
    testdir = os.path.join(os.environ['WASM_SPEC_DIR'], 'test', 'core')
    for fname in sorted(os.listdir(testdir)):
        if fname.endswith('.wast'):
            perform_test(os.path.join(testdir, fname))
