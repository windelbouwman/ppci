import unittest

from sample_helpers import add_samples, build
from util import has_qemu, qemu, relpath
from util import do_long_tests, make_filename
from ppci.format import uboot_image


@unittest.skipUnless(do_long_tests('microblaze'), 'skipping slow tests')
@add_samples('simple', 'medium')
class MicroblazeSamplesTestCase(unittest.TestCase):
    march = "microblaze"
    opt_level = 2

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'microblaze', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'microblaze', 'crt0.asm')
        mmap = relpath('..', 'examples', 'microblaze', 'layout.mmp')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='bin', code_image='flash')
        binfile = base_filename + '.bin'

        if has_qemu():
            output = qemu([
                'qemu-system-microblaze', '-nographic',
                '-M', 'or1k-sim', '-m', '16',
                '-kernel', img_filename])
            self.assertEqual(expected_output, output)
