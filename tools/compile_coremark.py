"""Compile coremark benchmark.


https://github.com/eembc/coremark

"""

import glob
import os
import io
from ppci import api, __version__ as ppci_version
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

home = os.environ["HOME"]
core_mark_folder = os.path.join(home, "GIT", "coremark")
this_dir = os.path.abspath(os.path.dirname(__file__))
port_folder = os.path.join(core_mark_folder, "linux64")
libc_folder = os.path.join(this_dir, "..", "librt", "libc")
linux64_folder = os.path.join(this_dir, "..", "examples", "linux64")

opt_level = 2
march = api.get_arch("x86_64")
coptions = COptions()
coptions.add_include_path(core_mark_folder)
coptions.add_include_path(port_folder)
coptions.add_include_path(os.path.join(libc_folder, "include"))
coptions.add_define("COMPILER_VERSION", '"ppci {}"'.format(ppci_version))
coptions.add_define("FLAGS_STR", '"-O{}"'.format(opt_level))

# Prevent malloc / free usage:
coptions.add_define("MEM_METHOD", "MEM_STATIC")

# TODO: Hack to enable %f formatting:
coptions.add_define("__x86_64__", "1")

objs = []

crt0_asm = os.path.join(linux64_folder, "glue.asm")
crt0_c3 = os.path.join(linux64_folder, "bsp.c3")
linker_script = os.path.join(linux64_folder, "linux64.mmap")
objs.append(api.asm(crt0_asm, march))
objs.append(api.c3c([crt0_c3], [], march))
objs.append(api.cc(io.StringIO(hacked_libc_extras), march, coptions=coptions))

sources = list(glob.glob(os.path.join(core_mark_folder, "*.c")))
sources.extend(glob.glob(os.path.join(port_folder, "*.c")))
sources.extend(glob.glob(os.path.join(libc_folder, "*.c")))

for source_file in sources:
    print(source_file)
    try:
        with open(source_file, "r") as f:
            obj = api.cc(f, march, coptions=coptions, opt_level=opt_level)
    except CompilerError as ex:
        print("ERROR!")
        print(ex)
        ex.print()
    else:
        objs.append(obj)

print(objs)

full_obj = api.link(objs, layout=linker_script)

exe_filename = "coremark.elf"
with open(exe_filename, "wb") as f:
    write_elf(full_obj, f)

api.chmod_x(exe_filename)
