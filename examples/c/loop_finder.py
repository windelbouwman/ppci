""" Find loops in a Ir program by usage of the dominator tree """

import io
import os
from ppci.lang.c import COptions
from ppci.api import c_to_ir, get_arch, optimize
from ppci.irs.wasm import ir_to_wasm, export_wasm_example

this_dir = os.path.dirname(os.path.abspath(__file__))
arch = get_arch('arm')
coptions = COptions()
libc_dir = os.path.join(this_dir, '..', '..', 'librt', 'libc')
coptions.add_include_path(libc_dir)

# Compile c source:

#with open(os.path.join(libc_dir, 'lib.c')) as f:
#    x = c_to_ir(f, arch, coptions=coptions)
# Simple C program:
f = io.StringIO("""
int add(int a, int b) {
 return a + b + 133;
}

int sub(int a, int b) {
/*
  while (a > 2) {
    a--;
  }*/
  return add(a, b) - 133;
}

""")
x = c_to_ir(f, arch, coptions=coptions)
print(x, x.stats())
optimize(x, level='2')
print(x, x.stats())

x.display()

wasm_module = ir_to_wasm(x)

print(wasm_module)
wasm_module.show()
print(wasm_module.to_bytes())

html_filename = os.path.join(this_dir, 'wasm_demo.html')
src = 'source'
main_js = """
print_ln(module.exports.add(2,5));
print_ln(module.exports.sub(2,5));
"""
export_wasm_example(html_filename, src, wasm_module, main_js=main_js)
