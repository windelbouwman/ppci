
import io
import os
import logging
from ppci.lang.c import COptions
from ppci.api import c_to_ir, get_arch, optimize
from ppci.irs.wasm import ir_to_wasm, export_wasm_example

logging.basicConfig(level=logging.DEBUG)
this_dir = os.path.dirname(os.path.abspath(__file__))
wasm_filename = os.path.join(this_dir, 'samples_in_wasm.wasm')
arch = get_arch('arm')
coptions = COptions()
libc_dir = os.path.join(this_dir, '..', 'librt', 'libc')
coptions.add_include_path(libc_dir)

libc_filename = os.path.join(
    this_dir, '..', 'librt', 'libc', 'lib.c')

def c_to_wasm(filename):
    # Compile c source:
    with open(libc_filename, 'r') as f:
        ir_libc = c_to_ir(f, arch, coptions=coptions)

    print(ir_libc, ir_libc.stats())
    optimize(ir_libc, level='2')

    with open(filename, 'r') as f:
        x = c_to_ir(f, arch, coptions=coptions)

    print(x, x.stats())
    optimize(x, level='2')
    print(x, x.stats())

    x.display()

    wasm_module = ir_to_wasm([ir_libc, x])

    print('Completed generating wasm module', wasm_module)
    wasm_module.show()
    print(wasm_module.to_bytes())
    with open(wasm_filename, 'wb') as f:
        wasm_module.to_file(f)
    return wasm_module


filename = os.path.join(
    this_dir, '..', 'test', 'samples', 'simple', 'jitsample.c')

wasm_module = c_to_wasm(filename)
html_filename = os.path.join(this_dir, 'samples_in_wasm.html')
src = 'source'
main_js = """
print_ln(module.exports.main_main());
"""
export_wasm_example(html_filename, src, wasm_module, main_js=main_js)

