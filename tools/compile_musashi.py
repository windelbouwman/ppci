""" Helper script to build Musashi (an M680x0 emulator)

Usage:

- clone the sourcecode with git:
https://github.com/kstenerud/Musashi
- Run this script

"""

import sys
import os
import logging
import time
import traceback
from ppci.api import cc, link
from ppci.lang.c import COptions
from ppci.common import CompilerError, logformat

home = os.environ['HOME']
src_folder = os.path.join(home, 'GIT', 'Musashi')
this_dir = os.path.abspath(os.path.dirname(__file__))
libc_path = os.path.join(this_dir, '..', 'librt', 'libc')
libc_includes = os.path.join(libc_path, 'include')
arch = 'x86_64'


def do_compile(filename):
    coptions = COptions()
    include_paths = [
        libc_includes,
        src_folder,
        ]
    coptions.add_include_paths(include_paths)
    with open(filename, 'r') as f:
        obj = cc(f, arch, coptions=coptions)
    return obj


def main():
    t1 = time.time()
    failed = 0
    passed = 0
    sources = [
        'm68kcpu.c',
        'm68kdasm.c',
    ]
    objs = []
    for filename in sources:
        filename = os.path.join(src_folder, filename)
        print('      ======================')
        print('    ========================')
        print('  ==> Compiling', filename)
        try:
            obj = do_compile(filename)
            objs.append(obj)
        except CompilerError as ex:
            print('Error:', ex.msg, ex.loc)
            ex.print()
            traceback.print_exc()
            failed += 1
        except Exception as ex:
            print('General exception:', ex)
            traceback.print_exc()
            failed += 1
        else:
            print('Great success!')
            passed += 1

    t2 = time.time()
    elapsed = t2 - t1
    print('Passed:', passed, 'failed:', failed, 'in', elapsed, 'seconds')
    obj = link(objs)
    print(obj)


if __name__ == '__main__':
    verbose = '-v' in sys.argv
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format=logformat)
    main()
