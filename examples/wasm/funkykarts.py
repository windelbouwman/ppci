from ppci.wasm import Module

# Download this file:
# https://www.funkykarts.rocks/demo.wasm

with open('funkykarts.wasm', 'rb') as f:
    m = Module(f.read())


print(m)
