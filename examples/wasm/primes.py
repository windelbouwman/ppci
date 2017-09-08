"""
Example that compiles Python code to WASM, then WASM to PPCI-IR, then to native,
and run in-process.
"""

import os
import sys
import logging
from io import StringIO
from time import perf_counter

from ppci import irutils
from ppci.api import ir_to_object, get_current_platform, get_arch, link, optimize
from ppci.utils import codepage, reporting, ir2py
from ppci.binutils import debuginfo

from ppci.irs.wasm import wasm_to_ppci
from ppci.lang.python import py_to_wasm

logging.basicConfig(level=logging.DEBUG)


## Example Python code
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
max = 4000
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

ARCH = get_arch('x86_64:wincc')  # todo: fix auto detecting arch on Windows

# Convert Python to wasm
wasm_module = py_to_wasm(py3)

# Convert wasm to ppci
debug_db = debuginfo.DebugDb()
ppci_module = wasm_to_ppci(wasm_module, debug_db=debug_db)

# Optimizer fails, or makes it slower ;)
# optimize(ppci_module, 2)

# Write IR code
f = StringIO()
irutils.Writer(f).write(ppci_module, verify=False)
print(f.getvalue())

# Compile to native object, while generating a report
with open(os.path.expanduser('~/ppci_report.html'), 'w') as f, reporting.HtmlReportGenerator(f) as reporter:
    ob = ir_to_object([ppci_module], ARCH, debug=True, debug_db=debug_db, reporter=reporter)
native_module = codepage.load_obj(ob)

# Run in memory
t0 = perf_counter()
result = native_module.main()
etime = perf_counter() - t0
print(f'native says {result} in {etime} s')

# Convert PPCI IR to (ugly) Python to skip codegen
if False:
    f = StringIO()
    pythonizer = ir2py.IrToPython(f)
    pythonizer.header()
    pythonizer.generate(ppci_module)
    py_code = f.getvalue()
    exec(py_code)
    print('python says', main())
