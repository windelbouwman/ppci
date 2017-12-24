import io
import unittest

from ppci import api, ir
from ppci.irs.wasm import wasm_to_ir, ir_to_wasm
from ppci.lang.python import python_to_wasm
from ppci.utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ppci.utils.leb128 import signed_leb128_decode, unsigned_leb128_decode


class WasmGeneratorTestCase(unittest.TestCase):
    def test_single_sample(self):
        src = io.StringIO("""
        int add(int a, int b) {
          int g = a+b+55+1-2;
          return g + a+8*b;
        }
        """)
        mod = api.c_to_ir(src, 'x86_64')
        # For now optimize to the allocation of a variable on heap:
        api.optimize(mod, level='2')
        wasm_module = ir_to_wasm(mod)
        # W00t! Convert back to ir again! (because it is possible)
        # TODO, make below work:
        # mod2 = wasm_to_ir(wasm_module)
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
        ir_mod = wasm_to_ir(wasm_module)
        self.assertIsInstance(ir_mod, ir.Module)


class Leb128TestCase(unittest.TestCase):
    """ Test examples from https://en.wikipedia.org/wiki/LEB128 """
    def test_unsigned_encoding_example(self):
        data = unsigned_leb128_encode(624485)
        self.assertEqual(bytes([0xe5, 0x8e, 0x26]), data)
        self.assertEqual(624485, unsigned_leb128_decode(iter(data)))

    def test_signed_encoding_example(self):
        data = signed_leb128_encode(-624485)
        self.assertEqual(bytes([0x9b, 0xf1, 0x59]), data)
        self.assertEqual(-624485, signed_leb128_decode(iter(data)))

    def test_signed_encoding_two(self):
        data = signed_leb128_encode(2)
        self.assertEqual(bytes([0x2]), data)
        self.assertEqual(2, signed_leb128_decode(iter(data)))

    def test_signed_encoding_minus_two(self):
        data = signed_leb128_encode(-2)
        self.assertEqual(bytes([0x7e]), data)
        self.assertEqual(-2, signed_leb128_decode(iter(data)))


if __name__ == '__main__':
    unittest.main(verbosity=1)
