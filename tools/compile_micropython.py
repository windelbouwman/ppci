
""" Helper script to compile micropython.

"""

import os
import logging
import glob
import time
import traceback
from ppci.api import cc
from ppci.lang.c import COptions
from ppci.common import CompilerError, logformat

home = os.environ['HOME']
micropython_folder = os.path.join(home, 'GIT', 'micropython')
this_dir = os.path.abspath(os.path.dirname(__file__))
libc_includes = os.path.join(this_dir, '..', 'librt', 'libc')
port_folder = os.path.join(micropython_folder, 'ports', 'bare-arm')
arch = 'arm'


def do_compile(filename):
    include_paths = [
        # os.path.join(newlib_folder, 'libc', 'include'),
        # TODO: not sure about the include path below for stddef.h:
        # '/usr/lib/gcc/x86_64-pc-linux-gnu/7.1.1/include'
        libc_includes,
        micropython_folder,
        port_folder,
        ]
    coptions = COptions()
    coptions.add_include_paths(include_paths)
    # coptions.add_define('NORETURN')
    with open(filename, 'r') as f:
        obj = cc(f, arch, coptions=coptions)
    return obj


def main():
    t1 = time.time()
    failed = 0
    passed = 0
    file_pattern = os.path.join(micropython_folder, 'py', '*.c')
    for filename in glob.iglob(file_pattern):
        print('==> Compiling', filename)
        try:
            do_compile(filename)
        except CompilerError as ex:
            print('Error:', ex.msg, ex.loc)
            ex.print()
            traceback.print_exc()
            failed += 1
            break
        except Exception as ex:
            print('General exception:', ex)
            traceback.print_exc()
            failed += 1
            break
        else:
            print('Great success!')
            passed += 1

    t2 = time.time()
    elapsed = t2 - t1
    print('Passed:', passed, 'failed:', failed, 'in', elapsed, 'seconds')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=logformat)
    main()
