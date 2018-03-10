"""
This script converts the rocket game what was written in rust:

https://github.com/aochagavia/rocket_wasm

Currently broken.

"""

import logging

from ppci.common import logformat
from ppci.wasm import read_wasm, wasm_to_ir


logging.basicConfig(level=logging.DEBUG, format=logformat)
with open('program.wasm', 'rb') as f:
    module = read_wasm(f)

# Save as binary:
with open('copy.wasm', 'wb') as f:
    module.to_file(f)

assert open('program.wasm', 'rb').read() == open('copy.wasm', 'rb').read()

# Save as text:
with open('wat.wat', 'w') as f:
    f.write(module.to_string())

print(module)
m2 = wasm_to_ir(module)

print(m2)
print(m2.stats())

