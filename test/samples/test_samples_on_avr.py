import unittest

from .sample_helpers import add_samples, build
from ..helper_util import has_avr_emulator, run_avr, relpath
from ..helper_util import do_long_tests, do_iverilog, make_filename


@unittest.skipUnless(do_long_tests("avr"), "skipping slow tests")
@add_samples("8bit", "simple")
class TestSamplesOnAvr(unittest.TestCase):
    march = "avr"
    opt_level = 0

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath("..", "examples", "avr", "bsp.c3")
        crt0 = relpath("..", "examples", "avr", "glue.asm")
        mmap = relpath("..", "examples", "avr", "avr.mmap")
        build(
            base_filename,
            src,
            bsp_c3,
            crt0,
            self.march,
            self.opt_level,
            mmap,
            lang=lang,
            bin_format="hex",
            code_image="flash",
        )
        hexfile = base_filename + ".hex"
        print(hexfile)
        if has_avr_emulator() and do_iverilog():
            res = run_avr(hexfile)
            self.assertEqual(expected_output, res)


# Avr Only works with optimization enabled...
class TestSamplesOnAvrO2(TestSamplesOnAvr):
    opt_level = 2
