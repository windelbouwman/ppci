""" Helper script to build links

Version: links-2.17

Usage:

- Download the links sourcecode from: http://links.twibright.com/download.php
- untar the sourcecode
- Set the environment variable LINKS_FOLDER to the unzipped dir
- Run this script

"""

import glob
import sys
import os
import logging
import time

try:
    from powertb import print_exc
except ImportError:
    from traceback import print_exc

from ppci.api import cc, link
from ppci.lang.c import COptions
from ppci.common import CompilerError, logformat
from ppci.utils.reporting import HtmlReportGenerator

links_folder = os.environ['LINKS_FOLDER']
this_dir = os.path.abspath(os.path.dirname(__file__))
report_filename = os.path.join(this_dir, 'report_links.html')
libc_includes = os.path.join(this_dir, '..', 'librt', 'libc')
arch = 'x86_64'


def do_compile(filename, coptions, reporter):
    with open(filename, 'r') as f:
        obj = cc(f, arch, coptions=coptions, reporter=reporter)
    return obj


def main():
    t1 = time.time()
    failed = 0
    passed = 0
    sources = glob.iglob(os.path.join(links_folder, '*.c'))
    objs = []
    coptions = COptions()
    include_paths = [
        libc_includes,
        links_folder,
        '/usr/include',
        ]
    coptions.add_include_paths(include_paths)
    with open(report_filename, 'w') as f, HtmlReportGenerator(f) as reporter:
        for filename in sources:
            filename = os.path.join(links_folder, filename)
            print('      ======================')
            print('    ========================')
            print('  ==> Compiling', filename)
            try:
                obj = do_compile(filename, coptions, reporter)
                objs.append(obj)
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
