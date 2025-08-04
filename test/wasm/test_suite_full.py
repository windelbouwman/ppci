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

Then, invoke this script with either pytest or run this script with python.
"""

# COOL IDEA: use python-requests to download the suite on demand to
# some temporary folder!

import unittest
import glob
import math
import os.path
import logging
from functools import reduce
from fnmatch import fnmatch
from operator import add
import argparse

from ppci.wasm import Module, instantiate, components
from ppci.common import CompilerError, logformat
from ppci.lang.sexpr import parse_s_expressions
from ppci.lang.sexpr import SExpression, SList
from ppci.utils.reporting import html_reporter
from ppci.wasm.util import datastring2bytes, unescape
from ppci.wasm.util import make_int, make_float


logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger()

# ==================== BLACKLISTS ==================== #

# TODO: at some point we should be able to process all snippets?
# Black list of test files
black_list = [
    # "linking",  # Requires linking. This does not work yet.
    "imports",  # Import support is too limited for now.
    # "elem",  # Importing of table not implemented
    # 'float_exprs',  # TODO: what is the issue here?
    # 'float_memory',  # TODO: handle signalling nan's
    # 'float_literals',  # TODO: handle nan's of all types.
    "skip-stack-guard-page",  # This is some stack overflow stuff?
    "func",  # TODO: this function is malformed!
]

# Black list of specific expressions, per file
black_list_expr = {
    "i64": [
        # Segfaults on too large positive integer:
        # This happens, since 9223372036854775808 = 0x8000000000000000 = 2^63
        # actually, this number is -2^63. Since the range of a 64 bit int
        # is from [-2^63 , 2^63) positive 2^63 is not included in the range.
        (
            "assert_return",
            (
                "invoke",
                "rem_s",
                ("i64.const", 9223372036854775808),
                ("i64.const", -1),
            ),
            ("i64.const", 0),
        ),
    ],
    "i32": [
        # Segfaults since remainder would be a too large integer:
        (
            "assert_return",
            ("invoke", "rem_s", ("i32.const", 2147483648), ("i32.const", -1)),
            ("i32.const", 0),
        ),
    ],
}


# ==================== END BLACKLISTS ==================== #


def perform_test(filename, target):
    logger.info("Loading %s", filename)
    base_name = os.path.splitext(os.path.split(filename)[1])[0]
    with open(filename, "rt", encoding="utf-8") as f:
        source_text = f.read()

    html_report = os.path.splitext(filename)[0] + "_" + target + ".html"
    with html_reporter(html_report) as reporter:
        reporter.message("Test spec file {}".format(filename))
        try:
            s_expressions = parse_s_expressions(source_text)
            expressions2ignore = black_list_expr.get(base_name, [])
            executor = WastExecutor(target, reporter, expressions2ignore)
            executor.execute(s_expressions)

        except CompilerError as ex:
            print("Exception:", ex)
            if ex.loc:
                lines = source_text.splitlines()
                ex.loc.filename = filename
                ex.render(lines)
            raise


class WastExecutor:
    """Execute a wasm spec test snippet.

    wast files are s-expression based webassembly
    snippets including test commands.
    """

    logger = logging.getLogger("wast-exe")

    def __init__(self, target, reporter, s_expr_blacklist):
        self.target = target
        self.reporter = reporter
        self.s_expr_blacklist = s_expr_blacklist

        # Parsed modules:
        self.last_mod = None
        self.named_modules = {}

        # Module instances:
        self.mod_instance = None
        self.named_module_instances = {}

        # Registered instances:
        self._registered_instances = {}

    def execute(self, s_expressions: tuple[SExpression]):
        for s_expr in s_expressions:
            if s_expr in self.s_expr_blacklist:
                self.logger.warning("Backlisted: %s", s_expr)
            else:
                self.execute_single(s_expr)

    def execute_single(self, s_expr: SList):
        """Execute a single line in the test case."""
        command = s_expr[0].get_symbol()
        if command == "module":
            self.load_module(s_expr)

        elif command == "invoke":
            # TODO: invoke test functions defined in wast files
            self.invoke(s_expr)

        elif command == "register":
            # TODO: register module for cross module imports.
            self.register_instance(s_expr)

        elif command == "assert_return":
            invoke_target = s_expr[1]
            expected_values = [self.parse_expr(e) for e in s_expr[2:]]

            if len(expected_values) == 0:
                self.evaluate(invoke_target)
            elif len(expected_values) == 1:
                expected_value = expected_values[0]
                if nan_or_inf(expected_value):
                    self.logger.warning(
                        "Not executing due to nan-or-inf %s", s_expr
                    )
                else:
                    result = self.evaluate(invoke_target)
                    self.assert_equal(result, expected_value)
            else:
                # TODO: implement multi return functions!
                self.logger.warning(
                    "Skipping multiple return function %s", invoke_target
                )
        elif command == "assert_trap":
            logger.debug("TODO: assert_trap")
        elif command == "assert_invalid":
            logger.debug("TODO: assert_invalid")
        elif command == "assert_malformed":
            logger.debug("TODO: assert_invalid")
        elif command == "assert_exhaustion":
            logger.debug("TODO: assert_exhaustion")
        else:
            # print('Unknown directive', s_expr[0])
            raise NotImplementedError(f"{command=}")

    def parse_module(self, s_expr: SList):
        """Parse a module from an s_expression"""
        if len(s_expr) > 1 and s_expr[1].is_symbol("binary"):
            m1 = self.parse_binary_module(s_expr)
        elif len(s_expr) > 2 and s_expr[2].is_symbol("binary"):
            m1 = self.parse_binary_module(s_expr)
            m1.id = s_expr[1].get_symbol()
        elif len(s_expr) > 1 and s_expr[1].is_symbol("quote"):
            m1 = self.parse_quoted_module(s_expr)
        else:
            m1 = self.parse_text_module(s_expr)
        self.logger.debug("loaded wasm module %s (id=%s)", m1, m1.id)
        return m1

    def parse_quoted_module(self, s_expr: SList):
        """Parse quoted module like: (module quote ....)"""
        strings = [unescape(s.value) for s in s_expr.values[2:]]
        # TODO: we might want to tokenize here, and re-use locations
        full_source = "(module " + reduce(add, strings) + ")"
        return Module(full_source)

    def parse_text_module(self, s_expr: SList):
        logger.debug(f"Loading text module at {s_expr.loc}")
        # Load module from tuples:
        m1 = Module(s_expr)

        # # Convert module to text form and parse again
        # # This should yield the same binary form:
        # m2 = Module(m1.to_string())
        # assert m1.to_bytes() == m2.to_bytes()

        # NOTE: going to string format and back does not
        # guarantee that parsing was correct.

        self.reporter.dump_wasm(m1)
        return m1

    def parse_binary_module(self, s_expr: SList) -> Module:
        logger.debug(f"Loading binary module at {s_expr.loc}")
        # We have (module binary "")

        # Iterate:
        elems = iter(s_expr)

        # Skip to binary tag:
        while not next(elems).is_symbol("binary"):
            pass

        # fetch data from last tuple elements:
        strings = map(lambda e: e.get_string(), elems)
        data = reduce(add, map(datastring2bytes, strings))

        # Load module from binary data:
        m1 = Module(data)

        # Go back
        data2 = m1.to_bytes()

        # Wont always be the same, e.g. some tests use non-minimal LEB ints
        # assert data == data2

        data3 = Module(data2).to_bytes()

        # Check that reading it in result in the same module ...
        assert data2 == data3
        return m1

    def load_module(self, s_expr):
        m1 = self.parse_module(s_expr)
        self.last_mod = m1
        if m1.id:
            self.named_modules[m1.id] = m1
        self.mod_instance = None

    def _instantiate(self, m1):
        """Instantiate a module."""
        # Next step: Instantiate:
        if self.target:

            def my_print() -> None:
                pass

            def print_i32(x: int) -> None:
                pass

            imports = {
                "spectest": {
                    "print_i32": print_i32,
                    "print": my_print,
                    #    'global_i32': 777,
                    "table": components.Table("$table", "funcref", 10, 20),
                }
            }

            for mod_name, reg_instance in self._registered_instances.items():
                imports[mod_name] = {}
                for export_name in reg_instance.exports:
                    obj = reg_instance.exports[export_name]
                    imports[mod_name][export_name] = obj

            mod_instance = instantiate(
                m1, imports=imports, target=self.target, reporter=self.reporter
            )
            self.logger.debug("Instantiated wasm module %s", mod_instance)
            if m1.id:
                self.named_module_instances[m1.id] = mod_instance
        else:
            mod_instance = None
        return mod_instance

    def evaluate(self, target: SExpression):
        if target[0].is_symbol("invoke"):
            return self.invoke(target)
        elif target[0].is_symbol("get"):
            return self.do_get(target)
        else:
            raise NotImplementedError(str(target[0]))

    def invoke(self, target: SExpression):
        """Invoke a function."""
        # print(target)
        assert target[0].is_symbol("invoke")
        # TODO: how to handle names like @#$%^&*?
        if (
            target[1].get_value().startswith("$")
            and len(target) > 2
            and isinstance(target[2].get_value(), str)
        ):
            module_id = target[1].get_value()
            instance = self.get_instance(module_id)
            func_name = target[2].get_value()
            args = target[3:]
        else:
            module_id = None
            instance = self.get_instance()
            func_name = target[1].get_value()
            args = target[2:]

        args = [self.parse_expr(a) for a in args]

        if not instance:
            self.logger.warning(
                "Skipping invoke, since no module instance was found"
            )
        elif any(nan_or_inf(a) for a in args):
            self.logger.warning(f"Not invoking method {func_name}({args})")
        else:
            self.logger.debug(f"Invoking {func_name} at line {target.loc}")
            return instance.exports[func_name](*args)

    def register_instance(self, s_expr):
        """register module for cross module imports."""
        assert s_expr[0].is_symbol("register")
        name = s_expr[1].get_string()
        self.logger.debug("Registering module %s", name)
        module_ref = s_expr[2].get_symbol() if len(s_expr) > 2 else None
        instance = self.get_instance(module_ref)
        if name in self._registered_instances:
            raise ValueError("Module {} already registered".format(name))
        else:
            self._registered_instances[name] = instance

    def do_get(self, target):
        """Get the value of a global variable."""
        assert target[0] == "get"
        if (
            target[1].startswith("$")
            and len(target) > 2
            and isinstance(target[2], str)
        ):
            module_id = target[1]
            instance = self.get_instance(module_id)
            var_name = target[2]
            assert len(target) == 3
        else:
            module_id = None
            instance = self.get_instance()
            var_name = target[1]
            assert len(target) == 2
        self.logger.debug("Getting global variable %s", var_name)
        global_var = instance.exports[var_name]
        return global_var.read()

    def get_instance(self, name=None):
        """Get a wasm module instance."""
        if name is None:
            if not self.mod_instance and self.last_mod:
                self.mod_instance = self._instantiate(self.last_mod)
            instance = self.mod_instance
        else:
            if (
                name not in self.named_module_instances
                and name in self.named_modules
            ):
                self.named_module_instances[name] = self._instantiate(
                    self.named_modules[name]
                )
            instance = self.named_module_instances[name]
        return instance

    @staticmethod
    def parse_expr(s_expr):
        """Evaluate a S-expression"""
        opcode = s_expr[0].get_symbol()
        if opcode in ["i32.const", "i64.const"]:
            bits = int(opcode[1:3])
            value = s_expr[1].get_symbol()
            return make_int(value, bits=bits)
        elif opcode in ["f32.const", "f64.const"]:
            value = s_expr[1].get_symbol()
            return make_float(value)
        elif opcode == "ref.extern":
            value = int(s_expr[1].get_symbol())
            return value
        elif opcode == "ref.null":
            return 0
        else:
            raise NotImplementedError(f"{opcode=}")

    def assert_equal(self, v1, v2):
        # print(v1, v2, type(v1), type(v2))
        logger.debug(f"Comparing {v1} == {v2}")
        if isinstance(v1, int) and isinstance(v2, int):
            assert v1 == v2
        elif isinstance(v1, float) and isinstance(v2, float):
            # TODO: is this margin acceptable?
            if math.isnan(v1):
                assert math.isnan(v2)
            elif math.isinf(v1) or math.isinf(v2):
                # TODO: implement better checking here
                self.logger.warning(
                    "assuming inf is equal to other large value"
                )
                return True
            else:
                assert math.isclose(v1, v2, rel_tol=0.0001, abs_tol=0.0000001)
        elif v1 is None:
            return True
        else:
            raise NotImplementedError(str(v1) + "=" + str(v2))


def nan_or_inf(x):
    return math.isnan(x) or math.isinf(x)


def create_test_function(cls, filename, target):
    """Create a test function for a single snippet"""
    core_test_directory, snippet_filename = os.path.split(filename)
    test_function_name = (
        "test_"
        + target
        + "_"
        + os.path.splitext(snippet_filename)[0]
        .replace(".", "_")
        .replace("-", "_")
    )

    def test_function(self):
        perform_test(filename, target)

    if hasattr(cls, test_function_name):
        raise ValueError("Duplicate test case {}".format(test_function_name))
    setattr(cls, test_function_name, test_function)


def wasm_spec_populate(cls):
    """Decorator function which can populate a unittest.TestCase class"""
    if "WASM_SPEC_DIR" in os.environ:
        wasm_spec_directory = os.path.normpath(os.environ["WASM_SPEC_DIR"])

        for target in ["python", "native"]:
            for filename in get_wast_files(wasm_spec_directory):
                create_test_function(cls, filename, target)
    else:

        def test_stub(self):
            self.skipTest(
                "Please specify WASM_SPEC_DIR if you wish to run the wasm spec"
                "test directory. "
                "For example: export WASM_SPEC_DIR=~/GIT/spec"
            )

        setattr(cls, "test_stub", test_stub)
    return cls


def get_wast_files(wasm_spec_directory, include_pattern="*"):
    """Retrieve wast files if WASM_SPEC_DIR was set"""
    # Do some auto detection:
    if os.path.isfile(os.path.join(wasm_spec_directory, "f32.wast")):
        core_test_directory = wasm_spec_directory
    else:
        core_test_directory = os.path.join(wasm_spec_directory, "test", "core")

    # Check if we have a folder:
    if not os.path.isdir(core_test_directory):
        raise ValueError("{} is not a directory".format(core_test_directory))

    # Check if we have the right folder:
    validation_file = os.path.join(core_test_directory, "f32.wast")
    if not os.path.exists(validation_file):
        raise ValueError("{} not found".format(validation_file))

    for filename in sorted(
        glob.iglob(os.path.join(core_test_directory, "*.wast"))
    ):
        # Ignore certain files:
        base_name = os.path.splitext(os.path.split(filename)[1])[0]
        if base_name in black_list:
            continue
        if not fnmatch(base_name, include_pattern):
            continue

        yield filename


@wasm_spec_populate
class WasmSpecTestCase(unittest.TestCase):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        choices=["native", "python"],
        action="append",
        default=[],
        help="The target for code generation.",
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument(
        "--filter",
        default="*",
        help="A filter pattern to select certain test cases.",
    )
    parser.add_argument(
        "spec_folder",
        help="the folder where the wasm spec test cases are located.",
    )
    args = parser.parse_args()

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)

    if args.target:
        for target in args.target:
            for filename in get_wast_files(
                args.spec_folder, include_pattern=args.filter
            ):
                perform_test(filename, target)
    else:
        print(
            "Specify at least one target environment, such as python or native"
        )

    print("OK.")
