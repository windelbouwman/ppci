""" Helper script to build libmad

Version: libmad-0.15.1b

Usage:

- Download the libmad sourcecode.
- Unzip the sourcecode
- Set the environment variable LIBMAD_FOLDER to the unzipped dir
- Run this script

"""

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
from ppci.utils.reporting import html_reporter


def do_compile(filename, include_paths, arch, reporter):
    coptions = COptions()
    coptions.add_include_paths(include_paths)
    coptions.add_define("FPM_DEFAULT", "1")
    with open(filename, "r") as f:
        obj = cc(f, arch, coptions=coptions, reporter=reporter)
    return obj


def main():
    environment_variable = "LIBMAD_FOLDER"
    if environment_variable in os.environ:
        libmad_folder = os.environ[environment_variable]
    else:
        logging.error(
            "Please define %s to point to the libmad source folder",
            environment_variable,
        )
        return

    this_dir = os.path.abspath(os.path.dirname(__file__))
    report_filename = os.path.join(this_dir, "report_libmad.html")
    libc_includes = os.path.join(this_dir, "..", "librt", "libc")
    include_paths = [libc_includes, libmad_folder]
    arch = "x86_64"

    t1 = time.time()
    failed = 0
    passed = 0
    sources = [
        "layer3.c",
        "version.c",
        "fixed.c",
        "bit.c",
        "timer.c",
        "stream.c",
        "frame.c",
        "synth.c",
        "decoder.c",
        "layer12.c",
        "huffman.c",
    ]
    objs = []
    with html_reporter(report_filename) as reporter:
        for filename in sources:
            filename = os.path.join(libmad_folder, filename)
            print("      ======================")
            print("    ========================")
            print("  ==> Compiling", filename)
            try:
                obj = do_compile(filename, include_paths, arch, reporter)
                objs.append(obj)
            except CompilerError as ex:
                print("Error:", ex.msg, ex.loc)
                ex.print()
                print_exc()
                failed += 1
            # except Exception as ex:
            #    print("General exception:", ex)
            #    print_exc()
            #    failed += 1
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
