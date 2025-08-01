import unittest

from .sample_helpers import add_samples, build
from ..helper_util import has_qemu, qemu, relpath
from ..helper_util import do_long_tests, make_filename


@unittest.skipUnless(do_long_tests("xtensa"), "skipping slow tests")
@add_samples("simple")
class TestSamplesOnXtensa(unittest.TestCase):
    march = "xtensa"
    opt_level = 0

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath("..", "examples", "xtensa", "bsp.c3")
        crt0 = relpath("..", "examples", "xtensa", "glue.asm")
        mmap = relpath("..", "examples", "xtensa", "layout.mmp")
        build(
            base_filename,
            src,
            bsp_c3,
            crt0,
            self.march,
            self.opt_level,
            mmap,
            lang=lang,
            bin_format="elf",
            code_image="flash",
        )
        elf_filename = base_filename + ".elf"
        if has_qemu():
            output = qemu(
                [
                    "qemu-system-xtensa",
                    "-nographic",
                    "-M",
                    "lx60",
                    "-m",
                    "16",
                    "-kernel",
                    elf_filename,
                ]
            )
            self.assertEqual(expected_output, output)
