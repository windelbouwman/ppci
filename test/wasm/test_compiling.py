""" Compile a piece of code to wasm, to ir, run it, compile back to wasm.
"""

from ppci import wasm
from ppci.lang.python import python_to_wasm
from ppci.api import ir_to_object, get_arch
from ppci.utils import codepage

# Example Python code
# A bit silly; they are assumed to be "main functions" so they can return a value

py1 = """
return 42
"""

py2 = """
a = 0
if 3 > 5:
    a = 41
elif 3 > 5:
    a = 5
else:
    a = 6
return a
"""

py3 = """
max = 400
n = 0
i = -1
gotit = 0
j = 0
# t0 = perf_counter()

while n < max:
    i = i + 1

    if i <= 1:
        continue  # nope
    elif i == 2:
        n = n + 1
    else:
        gotit = 1
        for j in range(2, i//2 + 1):
            if i % j == 0:
                gotit = 0
                break
        if gotit == 1:
            n = n + 1

# print(perf_counter() - t0)
# print(i)
return i
"""

## Run in memory


# disabled for now ...

def xx_test_compiling():

    # Convert Python to wasm
    wasm_module = python_to_wasm(py3)

    # Convert wasm to ppci
    ppci_module = wasm.wasm_to_ir(wasm_module)

    # Optimizer fails, or makes it slower ;)
    # optimize(ppci_module, 2)

    # Compile to native object
    arch = get_arch('x86_64:wincc')  # todo: fix auto detecting arch on Windows
    ob = ir_to_object([ppci_module], arch, debug=True)

    # Run in memory
    native_module = codepage.load_obj(ob)
    result = native_module.main()
    meeh = 1  # todo: if I remove this line, the test below fails :/
    # (ak: on my MSI, on my HP it always fails)
    assert result == 2741

    # Convert back to wasm
    # todo: cannot do this yet
    # wasm_module2 = wasm.ir_to_wasm(ppci_module)


if __name__ == '__main__':
    xx_test_compiling()
