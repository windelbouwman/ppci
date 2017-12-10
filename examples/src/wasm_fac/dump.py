
import io
from ppci.irs.wasm import read_wasm, wasm_to_wat


with open('fact.wasm', 'rb') as f:
    m = read_wasm(f)

print(m)

f = io.StringIO()
wasm_to_wat(m, f)
print(f.getvalue())
