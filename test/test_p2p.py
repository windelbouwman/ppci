from ppci import api
from ppci.irs.wasm.ppci2wasm import IrToWasmConvertor
import unittest
from unittest.mock import Mock
import io

from ppci.lang.python import load_py, python_to_ir

# Choose between those two:

src = """
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


@unittest.skipUnless(api.is_platform_supported(), 'skipping codepage tests')
class PythonJitLoadingTestCase(unittest.TestCase):
    """ Check the on the fly compiling of python code """
    def test_load_py(self):
        d = {}
        exec(src, d)
        a = d['a']
        m2 = load_py(io.StringIO(src))

        for x in range(20):
            v1 = a(x, 2)  # Python variant
            v2 = m2.a(x, 2)  # Compiled variant!
            self.assertEqual(v1, v2)

    @unittest.skip('todo')
    def test_callback(self):
        mock = Mock()
        def mp(x: int) -> None:
            mock(x)
        m2 = load_py(io.StringIO(src2), functions={'myprint': mp})
        m2.a(2)
        mck.assert_called_with(14)


class PythonToIrTranspilerTestCase(unittest.TestCase):
    """ Check the compilation of python code to ir """
    def test_snippet1(self):
        mod = python_to_ir(io.StringIO(src))

    @unittest.skip('todo')
    def test_snippet2(self):
        mod = python_to_ir(io.StringIO(src2))


if __name__ == '__main__':
    unittest.main()
