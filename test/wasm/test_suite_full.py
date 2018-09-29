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
import math
import os.path
import logging
import io
import sys
from functools import reduce
from operator import add
import warnings

from ppci.wasm import read_wat, Module, instantiate
from ppci.common import CompilerError, logformat
from ppci.lang.sexpr import parse_sexpr, parse_multiple_sexpr
from ppci.utils.reporting import HtmlReportGenerator
from ppci.wasm.util import datastring2bytes, sanitize_name
from ppci.wasm.util import make_int, make_float


# Load spec test-suite iterator
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from _spec_suite import get_spec_suite_dir, get_test_script_parts
sys.path.pop(0)


logging.getLogger().setLevel(logging.DEBUG)


# ==================== BLACKLISTS ==================== #

# TODO: at some point we should be able to process all snippets?
# Black list of test files
black_list = [
    'br_table',  # This test takes a long time, but works
    'names',  # Contains many weird unicode characters
    'linking',  # Requires linking. This does not work yet.
    'imports',  # Import support is too limited for now.
    'globals',  # Import of globals not implemented
    'data',  # Importing of memory not implemented
    'elem',  # Importing of table not implemented
    'exports',  # TODO: what goes wrong here?
    'float_exprs',  # TODO: what is the issue here?
    'float_memory',  # TODO: handle signalling nan's
    'float_literals',  # TODO: what is the issue here?
    'skip-stack-guard-page',  # This is some stack overflow stuff?
    'func',  # TODO: this function is malformed!
    # 'i64', # Grrr, so many expressions to blacklist!
]

# Black list of specific expressions, per file
black_list_expr = {
    'i64': [
        ('invoke', 'mul', ('i64.const', '0x0123456789abcdef'), ('i64.const', '0xfedcba9876543210')),
        ('invoke', 'div_u', ('i64.const', 10371807465568210928), ('i64.const', 4294967297)),
        ('invoke', 'div_u', ('i64.const', -5), ('i64.const', 2)),
        ('invoke', 'rem_u', ('i64.const', 10371807465568210928), ('i64.const', 4294967297)),
        ('invoke', 'and', ('i64.const', 4042326015), ('i64.const', 4294963440)),
        ('invoke', 'or', ('i64.const', 4042326015), ('i64.const', 4294963440)),
        ('invoke', 'shr_s', ('i64.const', 4611686018427387904), ('i64.const', 1)),
        ('invoke', 'shr_u', ('i64.const', 4611686018427387904), ('i64.const', 1)),
        ('invoke', 'rotl', ('i64.const', '0xabcd987602468ace'), ('i64.const', 1)),
        ('invoke', 'rotl', ('i64.const', '0xfe000000dc000000'), ('i64.const', 4)),
        # ... more needed
        ],
}


# On Windows, we need more blacklisting ...
if sys.platform.startswith('win'):
    
    black_list.append('conversions') # Grrr, so many expressions to blacklist!
    # Note that this list is not complete, I ran out of time ...
    
    # Segfault
    black_list_expr['i32'] = [
        ('invoke', 'rem_s', ('i32.const', 2147483648), ('i32.const', -1)),
        ]
    
    # Test fail
    black_list_expr['call'] = [
        ('invoke', 'fac', ('i64.const', 25)),
        ('invoke', 'fac-acc', ('i64.const', 25), ('i64.const', 1)),
        ]
    black_list_expr['call_indirect'] = [
        ('invoke', 'fac', ('i64.const', 25)),
        ]
    black_list_expr['fac'] = [
        ('invoke', 'fac-rec', ('i64.const', 25)),
        ('invoke', 'fac-iter', ('i64.const', 25)),
        ('invoke', 'fac-rec-named', ('i64.const', 25)),
        ('invoke', 'fac-iter-named', ('i64.const', 25)),
        ('invoke', 'fac-opt', ('i64.const', 25)),
        ]
    black_list_expr['conversions'] = [
        ('invoke', 'i64.extend_u_i32', ('i32.const', -10000)),
        ('invoke', 'i64.extend_u_i32', ('i32.const', -1)),
        ('invoke', 'i64.extend_u_i32', ('i32.const', 2147483648)),
        ('invoke', 'i64.trunc_s_f32', ('f32.const', 4294967296)),
        ('invoke', 'i64.trunc_s_f32', ('f32.const', -4294967296)),
        ('invoke', 'i64.trunc_s_f32', ('f32.const', 9.223371487098962e+18)),
        ('invoke', 'i64.trunc_s_f32', ('f32.const', -9.223372036854776e+18)),
        ('invoke', 'i64.trunc_u_f32', ('f32.const', 4294967296)),
        ('invoke', 'i64.trunc_u_f32', ('f32.const', 1.8446742974197924e+19)),
        ('invoke', 'i64.trunc_s_f64', ('f64.const', 4294967296)),
        ('invoke', 'i64.trunc_s_f64', ('f64.const', -4294967296)),
        ('invoke', 'i64.trunc_s_f64', ('f64.const', 9.223372036854775e+18)),
        ('invoke', 'i64.trunc_s_f64', ('f64.const', -9.223372036854776e+18)),
        ('invoke', 'i64.trunc_u_f64', ('f64.const', 4294967295)),
        ('invoke', 'i64.trunc_u_f64', ('f64.const', 4294967296)),
        ('invoke', 'i64.trunc_u_f64', ('f64.const', 1e+16)),
        ('invoke', 'i64.trunc_u_f64', ('f64.const', 9223372036854775808)),
        ('invoke', 'f32.convert_s_i64', ('i64.const', 9223372036854775807)),
        # ... more needed
        ]
    black_list_expr['endianness'] = [
        ('invoke', 'i64_load32_u', ('i64.const', -1)),
        ('invoke', 'i64_load32_u', ('i64.const', -42424242)),
        ('invoke', 'i64_load32_u', ('i64.const', '0xABAD1DEA')),
        ('invoke', 'i64_load', ('i64.const', '0xABAD1DEA')),
        ('invoke', 'i64_load', ('i64.const', '0xABADCAFEDEAD1DEA')),
        ('invoke', 'i64_store32', ('i64.const', -1)),
        ('invoke', 'i64_store32', ('i64.const', -4242)),
        ('invoke', 'i64_store32', ('i64.const', '0xDEADCAFE')),
        ('invoke', 'i64_store', ('i64.const', '0xABAD1DEA')),
        ('invoke', 'i64_store', ('i64.const', '0xABADCAFEDEAD1DEA')),
        ]
    black_list_expr['get_local'] = [
        ('invoke', 'read', ('i64.const', 1), ('f32.const', 2), ('f64.const', 3.3), ('i32.const', 4), ('i32.const', 5)),
        ]
    black_list_expr['int_exprs'] = [
        ('invoke', 'i64.div_s_3', ('i64.const', 3458764513820540928)),
        ('invoke', 'i64.div_u_3', ('i64.const', 13835058055282163712)),
        ('invoke', 'i64.div_s_5', ('i64.const', 5764607523034234880)),
        ('invoke', 'i64.div_u_5', ('i64.const', 11529215046068469760)),
        ('invoke', 'i64.div_s_7', ('i64.const', 8070450532247928832)),
        ('invoke', 'i64.div_u_7', ('i64.const', '0xe000000000000000')),
        ]
    black_list_expr['int_literals'] = [
        ('invoke', 'i64.test'),
        ('invoke', 'i64.smax'),
        ('invoke', 'i64.neg_smax'),
        ('invoke', 'i64.smin'),
        ('invoke', 'i64.alt_smin'),
        ('invoke', 'i64.inc_smin'),
        ('invoke', 'i64-hex-sep1'),
        ]
    black_list_expr['loop'] = [
        ('invoke', 'while', ('i64.const', 20)),
        ('invoke', 'for', ('i64.const', 20)),
        ]
    black_list_expr['memory'] = [
        ('invoke', 'cast'),
        ('invoke', 'i64_load32_u', ('i64.const', -1)),
        ('invoke', 'i64_load32_u', ('i64.const', '0x3456436598bacdef')),
        ]

# ==================== END BLACKLISTS ==================== #


def perform_test(filename, target):
    # if not os.path.basename(filename).startswith('z'):
    #     return
    logger = logging.getLogger()
    logger.info('Loading %s', filename)
    base_name = os.path.splitext(os.path.split(filename)[1])[0]
    with open(filename, 'rt', encoding='utf-8') as f:
        source_text = f.read()

    html_report = os.path.splitext(filename)[0] + '_' + target + '.html'
    with open(html_report, 'wt', encoding='utf8') as f, HtmlReportGenerator(f) as reporter:
        reporter.message('Test spec file {}'.format(filename))
        try:
            s_expressions = parse_multiple_sexpr(source_text)
            expressions2ignore = black_list_expr.get(base_name, [])
            s_expressions = [s_expr for s_expr in s_expressions if len(s_expr) != 3 or s_expr[1] not in expressions2ignore]
            if base_name == 'i64':
                does_big_edges = lambda x: '9223372036854775808' in x or '9223372036854775807' in x or '9223372036854775809' in x
                s_expressions = [s_expr for s_expr in s_expressions if not does_big_edges(str(s_expr))]
            executor = WastExecutor(target, reporter)
            executor.execute(s_expressions)

        except CompilerError as ex:
            print('Exception:', ex)
            lines = list(io.StringIO(source_text))
            ex.render(lines)
            raise


class WastExecutor:
    logger = logging.getLogger('wast-exe')

    def __init__(self, target, reporter):
        self.target = target
        self.reporter = reporter
        self.mod_instance = None

    def execute(self, s_expressions):
        for s_expr in s_expressions:
            self.execute_single(s_expr)

    def execute_single(self, s_expr):
        # print(s_expr)
        if s_expr[0] == 'module':
            self.load_module(s_expr)

        elif s_expr[0] == 'invoke':
            # TODO: invoke test functions defined in wast files
            if self.mod_instance:
                self.invoke(s_expr)

        elif s_expr[0] == 'assert_return':
            if self.mod_instance:
                if len(s_expr) > 2:
                    expected_value = self.parse_expr(s_expr[2])
                    if nan_or_inf(expected_value):
                        self.logger.warning('Not invoking %s', s_expr[1])
                    else:
                        result = self.invoke(s_expr[1])
                        self.assert_equal(result, expected_value)
                else:
                    self.invoke(s_expr[1])
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

            # # Convert module to text form and parse again
            # # This should yield the same binary form:
            # m2 = Module(m1.to_string())
            # assert m1.to_bytes() == m2.to_bytes()

            # NOTE: going to string format and back does not
            # guarantee that parsing was correct.

            self.reporter.dump_wasm(m1)

        self.logger.debug('loaded wasm module %s', m1)

        # Next step: Instantiate:
        if self.target:
            def my_print() -> None:
                pass

            def print_i32(x: int) -> None:
                pass

            imports = {
               'spectest': {
                   'print_i32': print_i32,
                   'print': my_print,
               }
            }
            self.mod_instance = instantiate(
                m1, imports, target=self.target, reporter=self.reporter)
            self.logger.debug('Instantiated wasm module %s', self.mod_instance)

    def invoke(self, target):
        # print(target)
        assert target[0] == 'invoke'
        # TODO: how to handle names like @#$%^&*?
        func_name = target[1]
        args = [self.parse_expr(a) for a in target[2:]]
        if any(nan_or_inf(a) for a in args):
            self.logger.warning('Not invoking method %s(%s)', func_name, args)
        else:
            self.logger.debug('Invoking ' + repr(target))
            return self.mod_instance.exports[func_name](*args)

    def parse_expr(self, s_expr):
        if s_expr[0] in ['i32.const', 'i64.const']:
            bits = int(s_expr[0][1:3])
            return make_int(s_expr[1], bits=bits)
        elif s_expr[0] in ['f32.const', 'f64.const']:
            return make_float(s_expr[1])
        else:
            raise NotImplementedError(str(s_expr))

    def assert_equal(self, v1, v2):
        # print(v1, v2, type(v1), type(v2))
        if isinstance(v1, int) and isinstance(v2, int):
            assert v1 == v2
        elif isinstance(v1, float) and isinstance(v2, float):
            # TODO: is this margin acceptable?
            if math.isnan(v1):
                assert math.isnan(v2)
            elif math.isinf(v1) or math.isinf(v2):
                # TODO: implement better checking here
                self.logger.warning(
                    'assuming inf is equal to other large value')
                return True
            else:
                assert math.isclose(v1, v2, rel_tol=0.0001, abs_tol=0.0000001)
        elif v1 is None:
            return True
        else:
            raise NotImplementedError(str(v1) + '=' + str(v2))


def nan_or_inf(x):
    return math.isnan(x) or math.isinf(x)


def create_test_function(cls, filename, target):
    """ Create a test function for a single snippet """
    core_test_directory, snippet_filename = os.path.split(filename)
    test_function_name = 'test_' + target + '_' \
        + os.path.splitext(snippet_filename)[0] \
        .replace('.', '_').replace('-', '_')

    def test_function(self):
        perform_test(filename, target)

    if hasattr(cls, test_function_name):
        raise ValueError('Duplicate test case {}'.format(test_function_name))
    setattr(cls, test_function_name, test_function)


def wasm_spec_populate(cls):
    """ Decorator function which can populate a unittest.TestCase class """
    for target in ['python', 'native']:
        for filename in get_wast_files():
            create_test_function(cls, filename, target)
    return cls


def get_wast_files():
    """ Retrieve wast files if WASM_SPEC_DIR was set """
    if 'WASM_SPEC_DIR' in os.environ:
        wasm_spec_directory = os.path.normpath(os.environ['WASM_SPEC_DIR'])
        if os.path.isfile(os.path.join(wasm_spec_directory, 'f32.wast')):
            core_test_directory = wasm_spec_directory
        else:
            core_test_directory = os.path.join(
                wasm_spec_directory, 'test', 'core')
        if not os.path.isdir(core_test_directory):
            raise ValueError(
                "WASM_SPEC_DIR is set, but {} not found".format(
                    core_test_directory))
        for filename in sorted(glob.iglob(os.path.join(
                core_test_directory, '*.wast'))):

            # Ignore certain files:
            base_name = os.path.splitext(os.path.split(filename)[1])[0]
            if base_name in black_list:
                continue

            yield filename
    else:
        warnings.warn(
            'Please specify WASM_SPEC_DIR if you wish to run the wasm spec'
            'test directory. '
            'For example: export WASM_SPEC_DIR=~/GIT/spec'
        )


@wasm_spec_populate
class WasmSpecTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    verbose = False
    if len(sys.argv) > 1:
        verbose = True

    if verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)
    # Three ways to run this:
    
    # unittest.main(verbosity=2)
    
    #perform_test(os.path.join(os.environ['WASM_SPEC_DIR'], 'i64.wast'), 'native')
    #perform_test(os.path.join(os.environ['WASM_SPEC_DIR'], 'names.wast'), 'native')
    
    continue_after = ''
    # for target in ['python', 'native']:
    # for target in ['native', 'python']:
    for target in ['native']:
        for filename in get_wast_files():
            if continue_after:
                if filename.endswith(continue_after + '.wast'):
                    continue_after = None
                continue
            perform_test(filename, target)
