import unittest

from sample_helpers import add_samples
from util import has_qemu, qemu, relpath, source_files
from util import do_long_tests, do_iverilog, make_filename


@unittest.skip('TODO')
@add_samples('8bit')
class TestSamplesOnStm8(unittest.TestCase):
    march = "stm8"
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'stm8', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'stm8', 'start.asm')
        mmap = relpath('..', 'examples', 'avr', 'avr.mmap')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='hex', code_image='flash')