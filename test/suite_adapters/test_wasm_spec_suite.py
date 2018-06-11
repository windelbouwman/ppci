"""
Run the tests as can be found here

https://github.com/WebAssembly/spec/tree/master/test

The directory structure of this spec is as follows:

- test
  - core
    - address.wast  -> test snippet in wasm text format with additional
      test info

To use these tests, clone https://github.com/WebAssembly/spec and set
the environment variable WASM_SPEC_DIR
to the location where the code was cloned.
"""

# COOL IDEA: use python-requests to download the suite on demand to
# some temporary folder!


import unittest
import glob
import os.path
import io
from functools import reduce
from operator import add

from ppci.wasm import read_wat, Module
from ppci.wasm.instantiate import instantiate, create_runtime
from ppci.common import CompilerError
from ppci.lang.sexpr import parse_sexpr, parse_multiple_sexpr
from ppci.utils.reporting import HtmlReportGenerator
from ppci.wasm.util import datastring2bytes


def perform_test(filename):
    # if not os.path.basename(filename).startswith('z'):
    #     return
    print(filename)
    with open(filename, 'rt', encoding='utf-8') as f:
        source_text = f.read()

    html_report = os.path.splitext(filename)[0] + '.html'
    with open(html_report, 'wt', encoding='utf8') as f, HtmlReportGenerator(f) as reporter:
        reporter.message('Test spec file {}'.format(filename))
        try:
            output_file = io.StringIO()
            s_expressions = parse_multiple_sexpr(source_text)
            for s_expr in s_expressions:
                # print(s_expr)
                if s_expr[0] == 'module':
                    if 'binary' in s_expr:
                        # We have (module binary "")

                        # Iterate:
                        elems = iter(s_expr)

                        # Skip to binary tag:
                        while next(elems) != 'binary':
                            pass

                        # fetch data from last tuple elements:
                        parts = []
                        for elem in elems:
                            data = datastring2bytes(elem)
                            parts.append(data)
                        data = reduce(add, parts)

                        # Load module from binary data:
                        m1 = Module(data)
                        
                        # Go back
                        data2 = m1.to_bytes()
                        
                        # Wont always be the same, e.g. some tests use non-minimal LEB ints
                        # assert data == data2
                        
                        data3 = Module(data2).to_bytes()
                        
                        # Check that reading it in result in the same module ...
                        assert data2 == data3
                    
                    else:
                        # Load module from tuples:
                        m1 = Module(s_expr)

                        # # Convert module to text form and parse again
                        # # This should yield the same binary form:
                        # m2 = Module(m1.to_string())
                        # assert m1.to_bytes() == m2.to_bytes()

                        # NOTE: going to string format and back does not
                        # guarantee that parsing was correct.

                        reporter.dump_wasm(m1)

                    # Next step: Instantiate:
                    if False:
                        imports = {
                           'rt': create_runtime(),
                        }
                        mod_instance = instantiate(
                            m1, imports, target='python', reporter=reporter)
                        print(mod_instance)

                elif s_expr[0] == 'invoke':
                    # TODO: invoke test functions defined in wast files
                    print('Invoking method', s_expr)
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
    
    # perform_test(r'C:\dev\wasm\spec\test\core\names.wast')
    
    testdir = os.path.join(os.environ['WASM_SPEC_DIR'], 'test', 'core')
    for fname in sorted(os.listdir(testdir)):
        if fname.endswith('.wast'):
            perform_test(os.path.join(testdir, fname))
