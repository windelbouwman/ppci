
""" Helper script to help in compilation of the newlib libc.

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
newlib_folder = os.path.join(home, 'GIT', 'newlib-cygwin', 'newlib')
cache_filename = os.path.join(newlib_folder, 'ppci_build.cache')


def do_compile(filename):
    include_paths = [
        os.path.join(newlib_folder, 'libc', 'include'),
        # TODO: not sure about the include path below for stddef.h:
        '/usr/lib/gcc/x86_64-pc-linux-gnu/7.1.1/include'
        ]
    coptions = COptions()
    coptions.add_include_paths(include_paths)
    coptions.add_define('HAVE_CONFIG_H')
    coptions.add_define('__MSP430__')
    with open(filename, 'r') as f:
        obj = cc(f, 'msp430', coptions=coptions)
    return obj


def main():
    t1 = time.time()
    print('Using newlib folder:', newlib_folder)
    crypt_md5_c = os.path.join(newlib_folder, 'src', 'crypt', 'crypt_md5.c')
    failed = 0
    passed = 0
    # file_pattern = os.path.join(newlib_folder, 'src', 'crypt', '*.c')
    # file_pattern = os.path.join(newlib_folder, 'src', 'string', '*.c')
    file_pattern = os.path.join(newlib_folder, 'libc', 'string', '*.c')
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
    logging.basicConfig(level=logging.INFO, format=logformat)
    main()
