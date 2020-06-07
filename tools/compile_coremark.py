""" Compile coremark benchmark.


https://github.com/eembc/coremark

"""

import glob
import os
import io
from ppci import api
from ppci.lang.c import COptions
from ppci.common import CompilerError
from ppci.format.elf import write_elf

# Custom provider for clock_gettime using linux syscall:
hacked_libc_extras = """

#include <time.h>

// Hack to enable clock_gettime in linux:

extern void bsp_syscall(int nr, int a, int b, int c);

int clock_gettime(clockid_t clockid, struct timespec *tp)
{
  // clock_gettime ==> syscall 228
  bsp_syscall(228, clockid, tp, 0);
  return 0;
}

// hack to route main_main to main:

extern main();
void main_main()
{
    main();
}

"""

home = os.environ['HOME']
core_mark_folder = os.path.join(home, 'GIT', 'coremark')
this_dir = os.path.abspath(os.path.dirname(__file__))
port_folder = os.path.join(core_mark_folder, 'linux64')
libc_folder = os.path.join(this_dir, "..", "librt", "libc")
linux64_folder = os.path.join(this_dir, '..', 'examples', 'linux64')

march = api.get_arch('x86_64')
coptions = COptions()
coptions.add_include_path(core_mark_folder)
coptions.add_include_path(port_folder)
coptions.add_include_path(libc_folder)
coptions.add_define('FLAGS_STR', '"-w0000t"')

objs = []

objs.append(api.asm(os.path.join(linux64_folder, 'glue.asm'), march))
objs.append(api.c3c([os.path.join(linux64_folder, 'bsp.c3')], [], march))
objs.append(api.cc(io.StringIO(hacked_libc_extras), march, coptions=coptions))

sources = list(glob.glob(os.path.join(core_mark_folder, '*.c')))
sources.extend(glob.glob(os.path.join(port_folder, '*.c')))
sources.extend(glob.glob(os.path.join(libc_folder, '*.c')))

for source_file in sources:
    print(source_file)
    try:
        with open(source_file, 'r') as f:
            obj = api.cc(f, march, coptions=coptions)
    except CompilerError as ex:
        print(ex)
        ex.print()
    else:
        objs.append(obj)

print(objs)

full_obj = api.link(objs)

with open('coremark.elf', 'wb') as f:
    write_elf(full_obj, f)
