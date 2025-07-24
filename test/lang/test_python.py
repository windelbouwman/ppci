import unittest
from unittest.mock import Mock
import io
from ppci import api, irutils
from ppci.lang.python import load_py, python_to_ir
from ppci.utils.reporting import html_reporter


src1 = """
def a(x: int, y: int) -> int:
    t = x + y
    if x > 10:
        return t
    else:
        if t > 5:
            return x - y + 100
        else:
            c = 55 - x
    return c
"""


src2 = """
def a(x: int) -> None:
    myprint(x + 13)
"""


src3 = """
def a2(x: int, y: int) -> int:
    return x + y

def a(x: int) -> int:
    return a2(x, 13)
"""


src4 = """
def test() -> int:
    a = 1
    return a
"""

src5 = """
def test() -> int:
  if 1 == 1:
    return 1
  return 2
"""

src6 = """
def p1(a: int):
    if a > 2:
        return

"""

src7 = """
def p1(a: str):
    if a == '3':
        return

"""


@unittest.skipUnless(api.is_platform_supported(), "skipping codepage tests")
class PythonJitLoadingTestCase(unittest.TestCase):
    """Check the on the fly compiling of python code"""

    def test_load_py(self):
        d = {}
        exec(src1, d)
        a = d["a"]
        with html_reporter("p2p_report.html") as reporter:
            m2 = load_py(io.StringIO(src1), reporter=reporter)

        for x in range(20):
            v1 = a(x, 2)  # Python variant
            v2 = m2.a(x, 2)  # Compiled variant!
            self.assertEqual(v1, v2)

    def test_callback(self):
        mock = Mock()

        def myprint(x: int) -> None:
            mock(x)

        imports = {
            "myprint": myprint,
        }
        with html_reporter("p2p_callback_report.html") as reporter:
            m2 = load_py(io.StringIO(src2), imports=imports, reporter=reporter)
        # Segfaults:
        m2.a(2)
        mock.assert_called_with(15)

    def test_multiple_functions(self):
        m2 = load_py(io.StringIO(src3))

        v2 = m2.a(2)
        self.assertEqual(15, v2)


class PythonToIrCompilerTestCase(unittest.TestCase):
    """Check the compilation of python code to ir"""

    def do(self, src, imports=None):
        mod = python_to_ir(io.StringIO(src), imports=imports)
        f = io.StringIO()
        irutils.print_module(mod, file=f)

        # Round trip test:
        irutils.read_module(io.StringIO(f.getvalue()))

    def test_snippet1(self):
        self.do(src1)

    def test_snippet2(self):
        imports = {"myprint": (None, (int,))}
        self.do(src2, imports=imports)
        # mod = python_to_ir(io.StringIO(src2), imports=imports)
        # print(f.getvalue())

    def test_snippet3(self):
        self.do(src3)

    def test_snippet4(self):
        self.do(src4)

    def test_snippet5(self):
        self.do(src5)

    def test_snippet6(self):
        self.do(src6)

    def test_snippet7(self):
        self.do(src7)


if __name__ == "__main__":
    unittest.main()
