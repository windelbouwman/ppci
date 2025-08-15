"""Test the ppci.wasm.instantiate function"""

import math
import unittest
from ppci.wasm import instantiate, Module
from ppci.api import is_platform_supported
from ppci.utils.reporting import html_reporter

# The below snippet is from the wasm spec test suite.
# It detected an issue in the x86_64 backend.
# The snippet contains calls to the wasm sqrt runtime function.
src = """
(module
  (func (export "f32.mul_sqrts") (param $x f32) (param $y f32) (result f32)
    (f32.mul (f32.sqrt (local.get $x)) (f32.sqrt (local.get $y))))

  (func (export "f64.mul_sqrts") (param $x f64) (param $y f64) (result f64)
    (f64.mul (f64.sqrt (local.get $x)) (f64.sqrt (local.get $y))))
)
"""


class WasmInstantiationTestCase(unittest.TestCase):
    def test_python_instantiation_f32_mul_sqrts(self):
        self.take_root(32, "python")

    def test_python_instantiation_f64_mul_sqrts(self):
        self.take_root(64, "python")

    @unittest.skipUnless(is_platform_supported(), "native code not supported")
    def test_native_instantiation_f32_mul_sqrts(self):
        self.take_root(32, "native")

    @unittest.skipUnless(is_platform_supported(), "native code not supported")
    def test_native_instantiation_f64_mul_sqrts(self):
        self.take_root(64, "native")

    def take_root(self, bits, target):
        # Function parameters and result:
        a = 4.0
        b = 9.0
        expected_result = 6.0

        # Python cross check:
        python_result = math.sqrt(a) * math.sqrt(b)
        assert math.isclose(
            python_result, expected_result, rel_tol=0.0001, abs_tol=0.0000001
        )

        # Now via wasm instantiation:
        module = Module(src)
        # report_filename = 'root_{}_{}.html'.format(bits, target)
        # with html_reporter(report_filename) as reporter:
        # , reporter=reporter)
        instance = instantiate(module, target=target)

        # print('root ', bits, 'instance', inst, 'for target', target)

        funcname = f"f{bits}.mul_sqrts"
        res = instance.exports[funcname](a, b)

        # print('Result:', res, 'expected=', expected_result, 'python says', python_result)

        assert math.isclose(
            res, expected_result, rel_tol=0.0001, abs_tol=0.0000001
        )

    def test_callbacks(self):
        """Test various stuff around wasm instantiation.
        See examples/wasm/callbacks.py
        """
        module = Module(
            (
                "import",
                "py",
                "add",
                ("func", "$add", ("param", "i64", "i64"), ("result", "i64")),
            ),
            (
                "global",
                "$g1",
                ("export", "var1"),
                ("mut", "i64"),
                ("i64.const", 42),
            ),
            (
                "func",
                ("export", "main"),
                ("param", "i64"),
                ("result", "i64"),
                ("local.get", 0),
                ("global.get", "$g1"),
                ("call", "$add"),
            ),
            (
                "func",
                ("export", "add"),
                ("param", "i64", "i64"),
                ("result", "i64"),
                ("local.get", 0),
                ("local.get", 1),
                ("call", "$add"),
            ),
            (
                "memory",
                ("export", "mem0ry"),
                ("data", "abcd"),
            ),
        )

        def my_add(x: int, y: int) -> int:
            print("my add called", x, y)
            return x + y + 1

        with html_reporter("oi.html") as reporter:
            instance = instantiate(
                module,
                imports={
                    "py": {
                        "add": my_add,
                    }
                },
                target="python",
                reporter=reporter,
            )

        self.assertEqual(1380, instance.exports.main(1337))
        self.assertEqual(85, instance.exports.add(42, 42))
        self.assertEqual(3, instance.exports["add"](1, 1))
        self.assertEqual(42, instance.exports.var1.read())
        instance.exports.var1.write(7)
        self.assertEqual(7, instance.exports.var1.read())
        self.assertEqual(1345, instance.exports.main(1337))
        self.assertEqual(b"abcd", instance.exports.mem0ry[0:4])
        instance.exports.mem0ry[1:3] = bytes([1, 2])
        self.assertEqual(b"a\x01\x02d", instance.exports.mem0ry[0:4])
