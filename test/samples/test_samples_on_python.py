import unittest
import io

from sample_helpers import add_samples, build_sample_to_ir
from helper_util import relpath, run_python
from helper_util import do_long_tests, make_filename

from ppci import api
from ppci.utils.reporting import HtmlReportGenerator
from ppci.irutils import print_module, read_module, to_json, from_json


@unittest.skipUnless(do_long_tests("python"), "skipping slow tests")
@add_samples("simple", "medium", "hard", "8bit", "fp", "double", "32bit")
class TestSamplesOnPython(unittest.TestCase):
    opt_level = 0

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        sample_filename = base_filename + ".py"
        list_filename = base_filename + ".html"

        bsp_c3 = io.StringIO(
            """
           module bsp;
           public function void putc(byte c);
           """
        )
        march = "arm"
        with HtmlReportGenerator(open(list_filename, "w")) as reporter:
            ir_modules = build_sample_to_ir(src, lang, bsp_c3, march, reporter)

            # Test roundtrip of ir_modules
            for ir_module in ir_modules:
                serialization_roundtrip(ir_module)
                api.optimize(
                    ir_module, level=self.opt_level, reporter=reporter
                )

            with open(sample_filename, "w") as f:
                api.ir_to_python(ir_modules, f, reporter=reporter)

                # Expose all functions as external symbols:
                for ir_module in ir_modules:
                    for routine in ir_module.functions:
                        print('_irpy_externals["{0}"] = {0}'.format(routine.name), file=f)

                # Add glue:
                print("", file=f)
                print("def bsp_putc(c):", file=f)
                print('    print(chr(c), end="")', file=f)
                print("", file=f)
                # print('_irpy_externals["printf"] = printf', file=f)
                print('_irpy_externals["bsp_putc"] = bsp_putc', file=f)
                print("", file=f)
                print("main_main()", file=f)
                print("", file=f)

        res = run_python(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnPythonO2(TestSamplesOnPython):
    opt_level = 2


def serialization_roundtrip(ir_module):
    f = io.StringIO()
    print_module(ir_module, file=f)
    txt1 = f.getvalue()
    print(txt1)

    # Round trip via json:
    d = to_json(ir_module)
    ir_module2 = from_json(d)

    f = io.StringIO()
    print_module(ir_module2, file=f)
    txt2 = f.getvalue()
    assert txt1 == txt2

    # Round trip via textual representation:
    f = io.StringIO(txt1)
    ir_module3 = read_module(f)

    f = io.StringIO()
    print_module(ir_module3, file=f)
    txt3 = f.getvalue()
    assert txt1 == txt3
