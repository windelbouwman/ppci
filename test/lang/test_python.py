import unittest
from unittest.mock import Mock
import io
from ppci import api, irutils
from ppci.lang.python import load_py, python_to_ir
from ppci.utils.reporting import HtmlReportGenerator


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


@unittest.skipUnless(api.is_platform_supported(), 'skipping codepage tests')
class PythonJitLoadingTestCase(unittest.TestCase):
    """ Check the on the fly compiling of python code """
    def test_load_py(self):
        d = {}
        exec(src1, d)
        a = d['a']
        with open('p2p_report.html', 'w') as f, \
                HtmlReportGenerator(f) as reporter:
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
            'myprint': myprint,
        }
        with open('p2p_callback_report.html', 'w') as f, \
                HtmlReportGenerator(f) as reporter:
            m2 = load_py(
                io.StringIO(src2), imports=imports, reporter=reporter)
        # Segfaults:
        m2.a(2)
        mock.assert_called_with(15)

    def test_multiple_functions(self):
        m2 = load_py(io.StringIO(src3))

        v2 = m2.a(2)
        self.assertEqual(15, v2)


class PythonToIrCompilerTestCase(unittest.TestCase):
    """ Check the compilation of python code to ir """
    def test_snippet1(self):
        python_to_ir(io.StringIO(src1))

    def test_snippet2(self):
        imports = {
            'myprint': (None, (int,))
        }
        mod = python_to_ir(io.StringIO(src2), imports=imports)
        f = io.StringIO()
        irutils.print_module(mod, file=f)
        # print(f.getvalue())

    def test_snippet3(self):
        python_to_ir(io.StringIO(src3))


if __name__ == '__main__':
    unittest.main()
