import io
import os
import unittest

from ppci import api, ir
from ppci.wasm import wasm_to_ir, ir_to_wasm, read_wasm
from ppci.lang.python import python_to_wasm


THIS_DIR = os.path.abspath(os.path.dirname(__file__))


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
# return i
"""


class WasmCompilerTestCase(unittest.TestCase):
    """ Test wasm to ir compiler """
    def test_wasm_primes_demo(self):
        """ Convert the primes demo into an ir module """
        wasm_module = python_to_wasm(py_primes)
        ir_mod = wasm_to_ir(wasm_module)
        self.assertIsInstance(ir_mod, ir.Module)


class WasmLoadAndSaveTestCase(unittest.TestCase):
    def test_load_save(self):
        """ Load program.wasm from disk and save it again. """
        program_filename = os.path.join(
            THIS_DIR, '..', '..', 'examples', 'wasm', 'program.wasm')
        with open(program_filename, 'rb') as f:
            wasm_module = read_wasm(f)

        with open(program_filename, 'rb') as f:
            content1 = f.read()

        # Save to file:
        f = io.BytesIO()
        wasm_module.to_file(f)
        content2 = f.getvalue()

        # Compare contents:
        self.assertEqual(content1, content2)


if __name__ == '__main__':
    unittest.main(verbosity=1)
