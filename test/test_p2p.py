from ppci import api
from ppci.utils.ir2wasm import IrToWasmConvertor
import unittest
import io

from ppci.utils.p2p import load_py

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


class P2pTestCase(unittest.TestCase):
    def test_p2p(self):
        d = {}
        exec(src, d)
        a = d['a']
        m2 = load_py(io.StringIO(src))

        for x in range(20):
            v1 = a(x, 2)  # Python variant
            v2 = m2.a(x, 2)  # Compiled variant!
            self.assertEqual(v1, v2)


if __name__ == '__main__':
    unittest.main()
