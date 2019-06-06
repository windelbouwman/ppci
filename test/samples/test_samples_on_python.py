import unittest
import io

from sample_helpers import add_samples
from helper_util import relpath, run_python
from helper_util import do_long_tests, make_filename

from ppci.api import c3_to_ir, bf_to_ir, ir_to_python, optimize, c_to_ir
from ppci.utils.reporting import HtmlReportGenerator
from ppci.lang.c import COptions


@unittest.skipUnless(do_long_tests('python'), 'skipping slow tests')
@add_samples('simple', 'medium', 'hard', '8bit', 'fp', 'double', '32bit')
class TestSamplesOnPython(unittest.TestCase):
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        sample_filename = base_filename + '.py'
        list_filename = base_filename + '.html'

        bsp = io.StringIO("""
           module bsp;
           public function void putc(byte c);
           """)
        march = 'arm'
        with HtmlReportGenerator(open(list_filename, 'w')) as reporter:
            if lang == 'c3':
                ir_modules = [c3_to_ir([
                    relpath('..', 'librt', 'io.c3'), bsp,
                    io.StringIO(src)], [], march, reporter=reporter)]
            elif lang == 'bf':
                ir_modules = [bf_to_ir(src, march)]
            elif lang == 'c':
                coptions = COptions()
                include_path1 = relpath('..', 'librt', 'libc')
                lib = relpath('..', 'librt', 'libc', 'lib.c')
                coptions.add_include_path(include_path1)
                with open(lib, 'r') as f:
                    mod1 = c_to_ir(
                        f, march,
                        coptions=coptions, reporter=reporter)
                mod2 = c_to_ir(
                    io.StringIO(src), march,
                    coptions=coptions, reporter=reporter)
                ir_modules = [mod1, mod2]
            else:  # pragma: no cover
                raise NotImplementedError(
                    'Language {} not implemented'.format(lang))

            for ir_module in ir_modules:
                optimize(ir_module, level=self.opt_level, reporter=reporter)

            with open(sample_filename, 'w') as f:
                ir_to_python(ir_modules, f, reporter=reporter)

                # Add glue:
                print('', file=f)
                print('def bsp_putc(c):', file=f)
                print('    print(chr(c), end="")', file=f)
                print('main_main()', file=f)

        res = run_python(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnPythonO2(TestSamplesOnPython):
    opt_level = 2
