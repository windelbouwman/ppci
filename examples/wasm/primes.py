"""
Example that compiles Python code to WASM, then WASM to PPCI-IR, then to native,
and run in-process.
"""

import os
import logging
from io import StringIO
from time import perf_counter

from ppci import irutils
from ppci.api import ir_to_object, get_current_arch
from ppci.utils import codepage, reporting

from ppci.wasm import wasm_to_ir, export_wasm_example
from ppci.lang.python import python_to_wasm, ir_to_python

logging.basicConfig(level=logging.DEBUG)


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

arch = get_current_arch()

# Convert Python to wasm
wasm_module = python_to_wasm(py3)

# Convert wasm to ppci
ppci_module = wasm_to_ir(wasm_module)

# Optimizer fails, or makes it slower ;)
# optimize(ppci_module, 2)

this_dir = os.path.dirname(os.path.abspath(__file__))
# Generate a report:
html_report = os.path.join(this_dir, 'compilation_report.html')
with open(html_report, 'w') as f, reporting.HtmlReportGenerator(f) as reporter:
    # Write IR code
    f = StringIO()
    irutils.print_module(ppci_module, file=f, verify=False)
    print(f.getvalue())

    # Compile to native object
    ob = ir_to_object([ppci_module], arch, debug=True, reporter=reporter)


# Hack: fix the return type
ob.debug_info.functions[0].return_type = float

# Run in memory
native_module = codepage.load_obj(ob)
t0 = perf_counter()
result = native_module.main()
etime = perf_counter() - t0
print(f'native says {result} in {etime} s')

# Generate html page:
export_wasm_example(
    os.path.join(this_dir, 'prime_demo_page.html'), py3, wasm_module)

# Convert PPCI IR to (ugly) Python to skip codegen
if True:
    f = StringIO()
    ir_to_python([ppci_module], f)
    py_code = 'def main():\n' + '\n'.join(['    ' + line for line in py3.splitlines()])
    exec(py_code)
    t0 = perf_counter()
    result = main()
    etime = perf_counter() - t0
    print(f'python says {result} in {etime}')
