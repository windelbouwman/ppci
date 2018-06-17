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
import logging
import io
from functools import reduce
from operator import add

from ppci.wasm import read_wat, Module
from ppci.wasm.instantiate import instantiate, create_runtime
from ppci.common import CompilerError, logformat
from ppci.lang.sexpr import parse_sexpr, parse_multiple_sexpr
from ppci.utils.reporting import HtmlReportGenerator
from ppci.wasm.util import datastring2bytes, sanitize_name


logging.getLogger().setLevel(logging.DEBUG)


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
            executor = WastExecutor(reporter)
            executor.execute(s_expressions)

            # TODO: check output for correct values:
            print(output_file.getvalue())
        except CompilerError as ex:
            print('Exception:', ex)
            lines = list(io.StringIO(source_text))
            ex.render(lines)
            raise


class WastExecutor:
    def __init__(self, reporter):
        self.reporter = reporter

    def execute(self, s_expressions):
        for s_expr in s_expressions:
            self.execute_single(s_expr)

    def execute_single(self, s_expr):
        # print(s_expr)
        if s_expr[0] == 'module':
            self.load_module(s_expr)

        elif s_expr[0] == 'invoke':
            # TODO: invoke test functions defined in wast files
            self.invoke(s_expr)

        elif s_expr[0] == 'assert_return':
            result = self.invoke(s_expr[1])
            if len(s_expr) > 2:
                expected_value = self.parse_expr(s_expr[2])
                assert result == expected_value
        else:
            # print('Unknown directive', s_expr[0])
            pass

    def load_module(self, s_expr):
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
            print(m1)

            # # Convert module to text form and parse again
            # # This should yield the same binary form:
            # m2 = Module(m1.to_string())
            # assert m1.to_bytes() == m2.to_bytes()

            # NOTE: going to string format and back does not
            # guarantee that parsing was correct.

            self.reporter.dump_wasm(m1)

        # Next step: Instantiate:
        if True:
            def my_print():
                pass

            def print_i32(x):
                pass

            imports = {
               'rt': create_runtime(),
               'spectest': {
                   'memory': True,  # TODO?
                   'global_i32': 1337,  # TODO?
                   'print_i32': print_i32,
                   'print': my_print,
               }
            }
            self.mod_instance = instantiate(
                m1, imports, target='python', reporter=self.reporter)
            print(self.mod_instance)

    def invoke(self, target):
        print(target)
        assert target[0] == 'invoke'
        # TODO: how to handle names like @#$%^&*?
        func_name = sanitize_name(target[1])
        args = [self.parse_expr(a) for a in target[2:]]
        print('Invoking method', func_name, args)
        return getattr(self.mod_instance.exports, func_name)(*args)

    def parse_expr(self, s_expr):
        if s_expr[0] == 'i32.const':
            return s_expr[1]
        elif s_expr[0] == 'i32.const':
            return s_expr[1]
        else:
            raise NotImplementedError(str(s_expr))


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
    for filename in get_wast_files():
        create_test_function(cls, filename)
    return cls


def get_wast_files():
    """ Retrieve wast files if WASM_SPEC_DIR was set """
    if 'WASM_SPEC_DIR' in os.environ:
        wasm_spec_directory = os.path.normpath(os.environ['WASM_SPEC_DIR'])
        core_test_directory = os.path.join(
            wasm_spec_directory, 'test', 'core')
        if not os.path.isdir(core_test_directory):
            raise ValueError(
                "WASM_SPEC_DIR is set, but {} not found".format(
                    core_test_directory))
        for filename in sorted(glob.iglob(os.path.join(
                core_test_directory, '*.wast'))):
            yield filename


@wasm_spec_populate
class WasmSpecTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    verbose = False
    if verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)
    # Three ways to run this:
    
    # unittest.main(verbosity=2)
    
    # perform_test(r'C:\dev\wasm\spec\test\core\names.wast')
    
    for filename in get_wast_files():
        perform_test(filename)
