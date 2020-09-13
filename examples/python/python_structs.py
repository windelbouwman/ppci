
import io
from ppci.api import ir_to_python, c_to_ir, get_arch, COptions, optimize


arch = get_arch('example')
bsp = io.StringIO("""
module bsp;
public function void sleep(int ms);
public function void putc(byte c);
public function bool get_key(int* key);
""")

coptions = COptions()
coptions.add_include_path('../../librt/libc/include')

sources = ['../src/structs/structs.c', '../../librt/libc/lib.c']
ir_modules = []
for source in sources:
    with open(source, 'r') as f:
        ir_module = c_to_ir(
            f, arch, coptions=coptions)
        optimize(ir_module, level=2)
        ir_modules.append(ir_module)

with open('generated_python_structs.py', 'w') as f:
    print('import time', file=f)
    print('import sys', file=f)
    print('import threading', file=f)
    ir_to_python(ir_modules, f)
    # Invoke main:
    print('def bsp_putc(c):', file=f)
    print('    print(chr(c), end="")', file=f)
    print('main_main()', file=f)
