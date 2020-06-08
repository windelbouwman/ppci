import unittest

from sample_helpers import add_samples, build
from helper_util import has_qemu, qemu, relpath
from helper_util import do_long_tests, make_filename
from ppci.format import uboot_image


@unittest.skipUnless(do_long_tests("microblaze"), "skipping slow tests")
@add_samples("simple", "medium")
class MicroblazeSamplesTestCase(unittest.TestCase):
    march = "microblaze"
    opt_level = 2

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath("..", "examples", "microblaze", "bsp.c3")
        crt0 = relpath("..", "examples", "microblaze", "crt0.asm")
        mmap = relpath("..", "examples", "microblaze", "layout.mmp")
        build(
            base_filename,
            src,
            bsp_c3,
            crt0,
            self.march,
            self.opt_level,
            mmap,
            lang=lang,
            bin_format="bin",
            code_image="flash",
        )
        bin_filename = base_filename + ".bin"

        if has_qemu():
            output = qemu(
                [
                    "qemu-system-microblaze",
                    "-nographic",
                    "-kernel",
                    bin_filename,
                ]
            )
            self.assertEqual(expected_output, output)
