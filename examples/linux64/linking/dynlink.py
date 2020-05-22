""" Example to show how to construct a dynamically share object.

DLL in windows world, SO in unix world.

"""

import io
from ppci import api
from ppci.format.elf import write_elf

c_src = r"""

/*
// enable this later!
int putchar(int);

// idea: link with libc for putchar!
void main()
{
    //putchar(65); // use libc, emit A
}
*/

int magic_helper(int x)
{
    return x + 1;
}

int barf(int x)
{
    return magic_helper(x) - 7;
}

"""



obj = api.cc(io.StringIO(c_src), 'x86_64')

print(obj)

with open('barf.o', 'wb') as f:
    write_elf(obj, f, type='relocatable')

