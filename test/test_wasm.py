import io
import unittest

from ppci import api, ir
from ppci.binutils import debuginfo
from ppci.irs.wasm.ppci2wasm import IrToWasmConvertor
from ppci.irs.wasm.wasm2ppci import wasm_to_ppci
from ppci.lang.python import python_to_wasm


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


py_primes = """
max = 4000
n = 0
i = -1
gotit = 0
j = 0
# t0 = perf_counter()

while n < max:
    i = i + 1
    
    if i <= 1:
        continue  # nope
    elif i == 2:
        n = n + 1
    else:
        gotit = 1
        for j in range(2, i//2 + 1):
            if i % j == 0:
                gotit = 0
                break
        if gotit == 1:
            n = n + 1

# print(perf_counter() - t0)
# print(i)
return i
"""


class WasmCompilerTestCase(unittest.TestCase):
    """ Test wasm to ir compiler """
    def test_wasm_primes_demo(self):
        """ Convert the primes demo into an ir module """
        wasm_module = python_to_wasm(py_primes)
        debug_db = debuginfo.DebugDb()
        ir_mod = wasm_to_ppci(wasm_module, debug_db=debug_db)
        self.assertIsInstance(ir_mod, ir.Module)


if __name__ == '__main__':
    unittest.main()
