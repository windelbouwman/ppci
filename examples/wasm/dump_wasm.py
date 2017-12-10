import logging

from ppci.irs.wasm import read_wasm, wasm_to_ir

logging.basicConfig(level=logging.DEBUG)
with open('program.wasm', 'rb') as f:
    module = read_wasm(f)

print(module)
m2 = wasm_to_ir(module)

print(m2)
print(m2.stats())

