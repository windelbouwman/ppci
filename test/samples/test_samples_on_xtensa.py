import unittest

from sample_helpers import add_samples, build
from util import has_qemu, qemu, relpath
from util import do_long_tests, make_filename


@unittest.skipUnless(do_long_tests('xtensa'), 'skipping slow tests')
@add_samples('simple')
class TestSamplesOnXtensa(unittest.TestCase):
    march = "xtensa"
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'xtensa', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'xtensa', 'glue.asm')
        mmap = relpath('..', 'examples', 'xtensa', 'layout.mmp')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='bin', code_image='flash')
        binfile = base_filename + '.bin'
        img_filename = base_filename + '.img'
        self.make_image(binfile, img_filename)
        if has_qemu():
            output = qemu([
                'qemu-system-xtensa', '-nographic',
                '-M', 'lx60', '-m', '16',
                '-drive',
                'if=pflash,format=raw,file={}'.format(img_filename)])
            self.assertEqual(expected_output, output)

    def make_image(self, bin_filename, image_filename, imagemb=4):
        with open(bin_filename, 'rb') as f:
            hello_bin = f.read()

        flash_size = imagemb * 1024 * 1024

        with open(image_filename, 'wb') as f:
            f.write(hello_bin)
            padding = flash_size - len(hello_bin)
            f.write(bytes(padding))
