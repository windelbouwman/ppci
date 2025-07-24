import io
import os
import unittest

from ppci.arch.arch_info import TypeInfo
from ppci import api, ir
from ppci.wasm import wasm_to_ir, ir_to_wasm, read_wasm, read_wat
from ppci.lang.python import python_to_wasm
from ppci.wasm.util import sanitize_name


THIS_DIR = os.path.abspath(os.path.dirname(__file__))


class WasmGeneratorTestCase(unittest.TestCase):
    def test_single_sample(self):
        src = io.StringIO(
            """
        int add(int a, int b) {
          int g = a+b+55+1-2;
          return g + a+8*b;
        }
        """
        )
        mod = api.c_to_ir(src, "x86_64")
        # For now optimize to the allocation of a variable on heap:
        api.optimize(mod, level="2")
        wasm_module = ir_to_wasm(mod)

        # W00t! Convert back to ir again! (because it is possible)
        mod2 = wasm_to_ir(
            wasm_module, api.get_arch("x86_64").info.get_type_info("ptr")
        )
        # TODO: find a way to execute this wasm code.
        ir_to_wasm(mod2)
        # Idea: maybe convert the wasm back to ir, and run that?


class WasmLoadAndSaveTestCase(unittest.TestCase):
    def test_load_save(self):
        """Load program.wasm from disk and save it again."""
        program_filename = os.path.join(
            THIS_DIR, "..", "..", "examples", "wasm", "program.wasm"
        )
        with open(program_filename, "rb") as f:
            wasm_module = read_wasm(f)

        with open(program_filename, "rb") as f:
            content1 = f.read()

        # Save to file:
        f = io.BytesIO()
        wasm_module.to_file(f)
        content2 = f.getvalue()

        # Compare contents:
        self.assertEqual(content1, content2)

    def test_load_save_via_text(self):
        """Round trip test via text format.

        This is a good stress/sanity test on both
        WAT generation and parsing.
        """
        program_filename = os.path.join(
            THIS_DIR, "..", "..", "examples", "wasm", "program.wasm"
        )

        with open(program_filename, "rb") as f:
            content1 = f.read()

        with open(program_filename, "rb") as f:
            wasm_module = read_wasm(f)

        # convert to text format:
        wat_text = wasm_module.to_string()

        # Parse text format:
        f = io.StringIO(wat_text)
        wasm_module2 = read_wat(f)
        content2 = wasm_module2.to_bytes()

        self.assertEqual(content1, content2)


class NameNormalizationTestCase(unittest.TestCase):
    def test_sanitize_name(self):
        self.assertEqual("HelloA20World", sanitize_name("Hello World"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
