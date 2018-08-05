"""
wasmboy.wasm was made using:
$ clone https://github.com/torch2424/wasmBoy
$ npm run build
$ copy the file dist/core/index.untouched.wasm
"""
import logging
import os
import time

from ppci.wasm import Module, instantiate
from ppci.wasm import wasm_to_ir
from ppci.api import get_arch, ir_to_object
from ppci.utils import reporting

logging.basicConfig(level=logging.INFO)

with open('wasmboy.wasm', 'rb') as f:
    wasm_module = Module(f.read())

wasm_module.show_interface()

def log(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> None:
    print('Log:', a, b, c, d, e, f, g)

this_dir = os.path.dirname(os.path.abspath(__file__))
html_report = os.path.join(this_dir, 'wasmboy_report.html')
with open(html_report, 'w') as f, reporting.HtmlReportGenerator(f) as reporter:
    x = instantiate(
        wasm_module,
        {'env': {'log': log}},
        target='native',
        reporter=reporter
    )

print('wasm instance', x, x.memory_size())
# Following this explanation: 
# https://github.com/torch2424/wasmBoy/wiki/%5BWIP%5D-Core-API

# Load in a game to CARTRIDGE_ROM_LOCATION
l = x.exports.CARTRIDGE_ROM_LOCATION
start = l.read()
print('rom_start', l, l.read(), start)
with open('cpu_instrs.gb', 'rb') as f:
    data = f.read()
size = len(data)
x.exports.memory[start:start+size] = data

# Config
x.exports.config(
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False
)

t1 = time.time()
N = 30
# Run loop:
for i in range(N):
    print('Iteration', i)
    # 1. Check audio:
    num_samples = x.exports.getNumberOfSamplesInAudioBuffer()
    print('num audio samples', num_samples)
    x.exports.clearAudioBuffer()
    res = x.exports.executeFrame()
    if res == 0:
        pass  # We fine
    elif res == -1:
        raise RuntimeError('Gameboy died')
    else:
        ValueError('Invalid return value from executeFrame')

t2 = time.time()
total = t2 - t1
per_loop = total / N
print('Ran {} loops in {} seconds ({} seconds per iteration'.format(N, total, per_loop))

if False:
    arch = get_arch('x86_64')
    ptr_info = arch.info.get_type_info('ptr')
    ir_module = wasm_to_ir(wasm_module, ptr_info)

    print(ir_module)
    print(ir_module.stats())

    obj = ir_to_object([ir_module], arch)

    print(obj)
