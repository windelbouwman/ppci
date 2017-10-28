import io
from time import time as perf_counter

from ppci.programs import C3Program
from ppci.binutils import debuginfo

# todo: this does not work yet. I'm sure Windel has this working in a minute

bsp = """
module bsp;
public function void sleep(int ms);
public function void putc(byte c);
public function bool get_key(int* key);
"""

c3 = """
module main;
import io;

const int grid_size = 5;

function void main()
{
    var int i;
    for (i = 0; i < grid_size; i += 1) {
        io.println("hello from c3. ");
    }
}
"""

io_module = open('../../librt/io.c3', 'rt').read()
includes = [io.StringIO(bsp)]

## Compiling

debug_db = debuginfo.DebugDb()

# Create X86Code instance, specifying all steps
native = C3Program(io_module, c3, debugdb=debug_db).to_ir(includes).to_x86(win=True)

# Turn IR into Python, for testing
native.previous('ir').to('python').run(globals())  # this injects main() in globals


## Reporting

# Report chain of representations that the code went through
print(native.chain)

# Show source code
print('========== C3 ==========')
print(native.source.get_report())

# Show IR
print('========== IR ==========')
print(native.previous().get_report())


## Running 

# Run in memory, using API that is the same for all MachineCode representations

t0 = perf_counter()

result = native.run_in_process()

etime = perf_counter() - t0
print('native says {} in {} s'.format(result, etime))
