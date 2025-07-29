import io
from ppci.wasm import read_wasm


with open("fact.wasm", "rb") as f:
    m = read_wasm(f)

print(m)
m.show()
