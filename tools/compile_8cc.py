""" Helper script to build 8cc

8cc is a small c99 compiler written in c99.

https://github.com/rui314/8cc

Usage:

- git clone the 8cc sourcecode.
- Set the environment variable LIBMAD_FOLDER to the unzipped dir
- Run this script

"""

import os
import logging
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
_8cc_folder = os.path.join(home, 'GIT', '8cc')
this_dir = os.path.abspath(os.path.dirname(__file__))
report_filename = os.path.join(this_dir, 'report_8cc.html')
libc_includes = os.path.join(this_dir, '..', 'librt', 'libc')
linux_include_dir = '/usr/include'
arch = 'x86_64'
coptions = COptions()
include_paths = [
    libc_includes,
    _8cc_folder,
    linux_include_dir,
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
    sources = [
        'cpp.c',
        'debug.c',
        'dict.c',
        'gen.c',
        'lex.c',
        'vector.c',
        'parse.c',
        'buffer.c',
        'map.c',
        'error.c',
        'path.c',
        'file.c',
        'set.c',
        'encoding.c',
    ]
    with open(report_filename, 'w') as f, HtmlReportGenerator(f) as reporter:
        for filename in sources:
            filename = os.path.join(_8cc_folder, filename)
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
