import unittest

from sample_helpers import add_samples, build
from helper_util import has_qemu, qemu, relpath, create_qemu_launch_script
from helper_util import do_long_tests, make_filename
from ppci.format import uboot_image


@unittest.skipUnless(do_long_tests("or1k"), "skipping slow tests")
@add_samples("simple", "medium")
class OpenRiscSamplesTestCase(unittest.TestCase):
    march = "or1k"
    opt_level = 2

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath("..", "examples", "or1k", "bsp.c3")
        crt0 = relpath("..", "examples", "or1k", "crt0.asm")
        mmap = relpath("..", "examples", "or1k", "layout.mmp")
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
        binfile = base_filename + ".bin"

        # Create a uboot application file:
        with open(binfile, "rb") as f:
            bindata = f.read()

        img_filename = base_filename + ".img"
        with open(img_filename, "wb") as f:
            uboot_image.write_uboot_image(
                f, bindata, arch=uboot_image.Architecture.OPENRISC
            )

        qemu_cmd = [
            "qemu-system-or1k",
            "-nographic",
            "-M",
            "or1k-sim",
            "-m",
            "16",
            "-kernel",
            img_filename,
        ]

        create_qemu_launch_script(base_filename + ".sh", qemu_cmd)
        if has_qemu():
            output = qemu(qemu_cmd)
            self.assertEqual(expected_output, output)
