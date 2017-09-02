import io
import unittest

from ppci import api
from ppci.utils.ir2wasm import IrToWasmConvertor


class WasmGeneratorTestCase(unittest.TestCase):
    def test_single_sample(self):
        pass
        src = io.StringIO("""
        int add(int a, int b) {
          int g = a+b+55+1-2;
          return g + a+8*b;
        }
        """)
        mod = api.c_to_ir(src, 'x86_64')
        c = IrToWasmConvertor()
        wasm_code = c.do(mod)
        # TODO: find a way to execute this wasm code.
        # Idea: maybe convert the wasm back to ir, and run that?


if __name__ == '__main__':
    unittest.main()
