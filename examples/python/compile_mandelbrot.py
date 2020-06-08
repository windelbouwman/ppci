""" Epic demo of compiling some python code together with some C code
into a linux executable file.

"""
import io
import logging

from ppci.lang.python import python_to_ir
from ppci.irutils import verify_module, print_module
from ppci.api import ir_to_object, link, cc, objcopy
from ppci.utils.reporting import HtmlReportGenerator

# logging.basicConfig(level=logging.INFO)

def puts(txt: str):
	pass

with open('mandelbrot_compilation_report.html', 'w') as f, HtmlReportGenerator(f) as reporter:
    with open('mandelbrot.py', 'r') as f:
        mod = python_to_ir(f, imports = {'puts': puts})
    
    with open('mandelbrot.py', 'r') as f:
        src = list(f)
    
    reporter.annotate_source(src, mod)


verify_module(mod)
# print_module(mod)

obj_py = ir_to_object([mod], 'x86_64')
# print(obj_py)

c_glue = """

void mandelbrot();
void syscall(long nr, long a, long b, long c);
void exit(int status);
void putc(char c);
void puts(char *s);

int main()
{
    mandelbrot();
    /* As we don't have any C startup code in this example, and main is
       the executable entrypoint, we can't just return, but have to
       call exit syscall explicitly. */
    exit(0);
}

void puts(char *s)
{
    while (*s) {
        putc(*s++);
    }
}

void putc(char c)
{
    syscall(1, 1, (long)&c, 1);
}

void exit(int status)
{
    syscall(60, status, 0, 0);
}

void syscall(long nr, long a, long b, long c)
{
    asm(
        "mov rax, %0 \n"
        "mov rdi, %1 \n"
        "mov rsi, %2 \n"
        "mov rdx, %3 \n"
        "syscall \n"
        :
        : "r" (nr), "r" (a), "r" (b), "r" (c) // input registers, patched into %0 .. %3
        : "rax", "rdi", "rsi", "rdx"  // clobber registers, handled by the register allocator
    );
}

"""

layout = """
ENTRY(main)

MEMORY code LOCATION=0x40000 SIZE=0x10000 {
    SECTION(code)
}

MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
    SECTION(data)
}
"""

obj_glue = cc(io.StringIO(c_glue), 'x86_64')

obj = link([obj_py, obj_glue], layout=io.StringIO(layout))
print(obj)

objcopy(obj, None, "elf", "mandelbrot")
