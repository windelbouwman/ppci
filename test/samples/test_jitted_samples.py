import unittest
import io

from .sample_helpers import add_samples, partial_build
from ..helper_util import do_long_tests, make_filename

from ppci.api import get_current_arch
from ppci.utils.codepage import load_obj
from ppci.utils.reporting import html_reporter


@unittest.skipUnless(do_long_tests("jit"), "skipping slow tests")
@add_samples("simple")
class TestJittedSamples(unittest.TestCase):
    """Take each sample, compile it and load it into the current process"""

    def do(self, src, expected_output, lang="c3"):
        # Compile:
        bsp_c3_src = """
        module bsp;
        public function void putc(byte c);
        """
        bsp_c3 = io.StringIO(bsp_c3_src)
        march = get_current_arch()
        base_filename = make_filename(self.id())
        report_filename = base_filename + ".html"
        with html_reporter(report_filename) as reporter:
            obj = partial_build(src, lang, bsp_c3, 0, march, reporter)

        actual_output = []

        def bsp_putc(c: int) -> None:
            # print('bsp_putc:', chr(c))
            actual_output.append(chr(c))

        # Dynamically load:
        imports = {
            "bsp_putc": bsp_putc,
        }
        mod = load_obj(obj, imports=imports)
        # print(dir(mod))

        # Invoke!
        if hasattr(mod, "main"):
            mod.main()
        else:
            mod.main_main()

        # Check output:
        actual_output = "".join(actual_output)
        self.assertEqual(expected_output, actual_output)


if __name__ == "__main__":
    unittest.main()
