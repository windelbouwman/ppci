import unittest
import io

from sample_helpers import add_samples
from helper_util import run_nodejs, relpath
from helper_util import do_long_tests, make_filename

from ppci.api import c3_to_ir, bf_to_ir, optimize, c_to_ir
from ppci.utils.reporting import HtmlReportGenerator
from ppci.lang.c import COptions
from ppci.wasm import ir_to_wasm
from ppci.ir_link import ir_link


@unittest.skipUnless(do_long_tests('wasm'), 'skipping slow tests')
@add_samples('simple', 'medium', 'fp')
class TestSamplesOnWasm(unittest.TestCase):
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        list_filename = base_filename + '.html'

        bsp = io.StringIO("""
           module bsp;
           public function void putc(byte c);
           """)
        march = 'arm'  # TODO: this must be wasm!
        with HtmlReportGenerator(open(list_filename, 'w')) as reporter:
            if lang == 'c3':
                ir_modules = [c3_to_ir([
                    bsp, relpath('..', 'librt', 'io.c3'),
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

            wasm_module = ir_to_wasm(ir_link(ir_modules), reporter=reporter)

        # Output wasm file:
        wasm_filename = base_filename + '.wasm'
        with open(wasm_filename, 'wb') as f:
            wasm_module.to_file(f)

        # Dat was 'm:
        wasm = wasm_module.to_bytes()
        wasm_text = str(list(wasm))
        wasm_data = 'var wasm_data = new Uint8Array(' + wasm_text + ');'

        # Output javascript file:
        js = NODE_JS_TEMPLATE.replace('JS_PLACEHOLDER', wasm_data)
        js_filename = base_filename + '.js'
        with open(js_filename, 'w') as f:
            f.write(js)

        # run node.js and compare output:
        res = run_nodejs(js_filename)
        self.assertEqual(expected_output, res)


NODE_JS_TEMPLATE = """
function bsp_putc(i) {
    var c = String.fromCharCode(i);
    process.stdout.write(c);
}

var providedfuncs = {
    bsp_putc: bsp_putc,
};

JS_PLACEHOLDER

function compile_my_wasm() {
    var module_ = new WebAssembly.Module(wasm_data);
    var module = new WebAssembly.Instance(module_, {js: providedfuncs});
    module.exports.main_main();
}

compile_my_wasm();
"""
