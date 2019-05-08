""" Helper script to build nOS

nOS is a RTOS for microcontrollers.

https://github.com/jimtremblay/nOS

Usage:

- git clone the nOS sourcecode.
- Run this script

"""

import glob
import logging
import os
import time

try:
    from powertb import print_exc
except ImportError:
    from traceback import print_exc

from ppci.api import cc
from ppci.utils.reporting import HtmlReportGenerator
from ppci.lang.c import COptions
from ppci.common import CompilerError, logformat

home = os.environ['HOME']
nos_folder = os.path.join(home, 'GIT', 'nOS')
nos_inc_folder = os.path.join(nos_folder, 'inc')
nos_src_folder = os.path.join(nos_folder, 'src')
this_dir = os.path.abspath(os.path.dirname(__file__))
report_filename = os.path.join(this_dir, 'report_nos.html')
libc_includes = os.path.join(this_dir, '..', 'librt', 'libc')
arch = 'msp430'
coptions = COptions()
coptions.enable('freestanding')
include_paths = [
    libc_includes,
    nos_inc_folder,
    os.path.join(nos_inc_folder, 'port', 'GCC', 'MSP430')
]
coptions.add_include_paths(include_paths)


def do_compile(filename, reporter):
    with open(filename, 'r') as f:
        obj = cc(f, arch, coptions=coptions, reporter=reporter)
    print(filename, 'compiled into', obj)
    return obj


def main():
    t1 = time.time()
    failed = 0
    passed = 0
    with open(report_filename, 'w') as f, HtmlReportGenerator(f) as reporter:
        for filename in glob.iglob(os.path.join(nos_src_folder, '*.c')):
            print('==> Compiling', filename)
            try:
                do_compile(filename, reporter)
            except CompilerError as ex:
                print('Error:', ex.msg, ex.loc)
                ex.print()
                print_exc()
                failed += 1
            except Exception as ex:
                print('General exception:', ex)
                print_exc()
                failed += 1
            else:
                print('Great success!')
                passed += 1

    t2 = time.time()
    elapsed = t2 - t1
    print(passed, 'passed,', failed, 'failed in', elapsed, 'seconds')


if __name__ == '__main__':
    verbose = False
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format=logformat)
    main()
