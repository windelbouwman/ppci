""" Primes example, now using high-level compiler pipeline.
"""

from time import perf_counter

from ppci.programs import PythonProgram  # or ppci.lang.python.PythonCode
from ppci.binutils import debuginfo


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


## Compiling

debug_db = debuginfo.DebugDb()

# Create X86Code instance, specifying all steps
native1 = PythonProgram(py3, debugdb=debug_db).to_wasm().to_ir().to_x86(win=True)

# native_arm = native1.previous().to_arm()

# Compile Python to X86 directly via ir - does not work atm
# native2 = PythonProgram(py3).to_ir().to_x86(win=True)

# Let PPCI figure out the compile chain
# native3 = PythonProgram(py3, debugdb=debug_db).to('x86', win=True)

native = native1

# >>> PythonProgram(py3).to('BF')
# ValueError: No compile chain possible from python to bf.

# Turn IR into Python, for testing
native.previous('ir').to('python').run(globals())  # this injects main() in globals


## Reporting

# Report chain of representations that the code went through
print(native.chain)

# Show source code
print('========== Python ==========')
print(native.source.get_report())

# Show WASM
print('========== WASM ==========')
print(native.previous('wasm').get_report())

# Show IR
print('========== IR ==========')
print(native.previous().get_report())


## Running 

# Run in memory, using API that is the same for all MachineCode representations

t0 = perf_counter()

result = native.run_in_process()

etime = perf_counter() - t0
print('native says {} in {} s'.format(result, etime))
