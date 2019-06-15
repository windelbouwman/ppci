""" Helper script to build lcc.

https://github.com/drh/lcc

Usage:

- Clone the lcc sourcecode.
- Set the environment variable LCC_FOLDER to the lcc source dir.
- Run this script

"""

import sys
import glob
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


def do_compile(filename, include_paths, arch, reporter):
    coptions = COptions()
    coptions.add_include_paths(include_paths)
    coptions.add_define("FPM_DEFAULT", "1")
    with open(filename, "r") as f:
        obj = cc(f, arch, coptions=coptions, reporter=reporter)
    return obj


def main():
    environment_variable = "LCC_FOLDER"
    if environment_variable in os.environ:
        lcc_folder = os.environ[environment_variable]
    else:
        logging.error(
            "Please define %s to point to the lcc source folder",
            environment_variable,
        )
        return

    this_dir = os.path.abspath(os.path.dirname(__file__))
    report_filename = os.path.join(this_dir, "report_lcc.html")
    libc_includes = os.path.join(this_dir, "..", "librt", "libc")
    include_paths = [
        libc_includes
    ]
    arch = "x86_64"

    t1 = time.time()
    failed = 0
    passed = 0
    sources = glob.glob(os.path.join(lcc_folder, 'src', '*.c'))
    objs = []
    with open(report_filename, "w") as f, HtmlReportGenerator(f) as reporter:
        for filename in sources:
            print("      ======================")
            print("    ========================")
            print("  ==> Compiling", filename)
            try:
                obj = do_compile(filename, include_paths, arch, reporter)
                objs.append(obj)
            except CompilerError as ex:
                print("Error:", ex.msg, ex.loc)
                ex.print()
                # print_exc()
                failed += 1
            except Exception as ex:
                print("General exception:", ex)
                # ex.print()
                print_exc()
                failed += 1
            else:
                print("Great success!")
                passed += 1

    t2 = time.time()
    elapsed = t2 - t1
    print("Passed:", passed, "failed:", failed, "in", elapsed, "seconds")
    obj = link(objs)
    print(obj)


if __name__ == "__main__":
    verbose = "-v" in sys.argv
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format=logformat)
    main()
