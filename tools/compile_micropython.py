""" Helper script to compile micropython.

Links to micropython: https://micropython.org/

"""

import os
import logging
import glob
import time

from ppci.api import cc
from ppci.lang.c import COptions
from ppci.common import CompilerError, logformat

try:
    from powertb import print_exc
except ImportError:
    from traceback import print_exc

home = os.environ['HOME']
micropython_folder = os.path.join(home, 'GIT', 'micropython')
this_dir = os.path.abspath(os.path.dirname(__file__))
libc_path = os.path.join(this_dir, '..', 'librt', 'libc')
libc_includes = os.path.join(libc_path, 'include')
port_folder = os.path.join(micropython_folder, 'ports', 'unix')
arch = 'arm'


def do_compile(filename, coptions):
    # coptions.add_define('NORETURN')
    with open(filename, 'r') as f:
        obj = cc(f, arch, coptions=coptions)
    return obj


def main():
    t1 = time.time()
    failed = 0
    passed = 0
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
    coptions.enable('freestanding')
    coptions.add_define('NO_QSTR', '1')
    file_pattern = os.path.join(micropython_folder, 'py', '*.c')
    objs = []
    for filename in glob.iglob(file_pattern):
        print('==> Compiling', filename)
        try:
            obj = do_compile(filename, coptions)
        except CompilerError as ex:
            print('Error:', ex.msg, ex.loc)
            ex.print()
            print_exc()
            failed += 1
            # break
        except Exception as ex:
            print('General exception:', ex)
            print_exc()
            failed += 1
            # break
        else:
            print('Great success!', obj)
            passed += 1
            objs.append(obj)

    t2 = time.time()
    elapsed = t2 - t1
    print('Passed:', passed, 'failed:', failed, 'in', elapsed, 'seconds')


if __name__ == '__main__':
    verbose = False
    if verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format=logformat)
    main()
