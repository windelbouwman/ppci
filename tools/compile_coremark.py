""" Compile coremark benchmark.


https://github.com/eembc/coremark

"""

import glob
import os
from ppci import api
from ppci.lang.c import COptions
from ppci.common import CompilerError


this_dir = os.path.abspath(os.path.dirname(__file__))
core_mark_folder = '/home/windel/GIT/coremark'
port_folder = os.path.join(core_mark_folder, 'linux64')
libc_folder = os.path.join(this_dir, "..", "librt", "libc")

arch = api.get_arch('x86_64')
coptions = COptions()
coptions.add_include_path(core_mark_folder)
coptions.add_include_path(port_folder)
coptions.add_include_path(libc_folder)
coptions.add_define('FLAGS_STR', '"-w0000t"')

sources = list(glob.glob(os.path.join(core_mark_folder, '*.c')))
sources.extend(glob.glob(os.path.join(port_folder, '*.c')))

objs = []
for source_file in sources:
    print(source_file)
    try:
        with open(source_file, 'r') as f:
            obj = api.cc(f, arch, coptions=coptions)
    except CompilerError as ex:
        print(ex)
        ex.print()
    else:
        objs.append(obj)

print(objs)

api.link(objs)
