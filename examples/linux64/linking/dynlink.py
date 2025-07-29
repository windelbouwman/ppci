"""Example to show how to construct a dynamically share object.

DLL in windows world, SO in unix world.

"""

import io
from ppci import api
from ppci.format.elf import write_elf

c_src = r"""

// This will trigger relocations on the data section:
double a;
double *pa = &a;

// idea: link with libc for putchar!
int putchar(int);

int magic_helper(int x)
{
    putchar(65); // 'A'
    return x + 1 + *pa;
}

int barf(int x, double y)
{
    putchar(66); // 'B'
    return magic_helper(x) - y;
}

"""


obj = api.cc(io.StringIO(c_src), "x86_64")

print(obj)

with open("barf.o", "wb") as f:
    write_elf(obj, f, type="relocatable")
