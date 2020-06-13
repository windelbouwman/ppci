""" Unit test adapter for c-testsuite

The c-testsuite is a collection of C test cases.

This is an adapter script to enable running of those snippets
as unittests.

Usage with pytest:

    $ export C_TEST_SUITE_DIR=/path/to/GIT/c-testsuite
    $ python -m pytest test_c_test_suite.py -v

Usage as a script:

    $ python test_c_test_suite.py /path/to/GIT/c-testsuite

See also:

https://github.com/c-testsuite/c-testsuite

"""


import unittest
import glob
import fnmatch
import argparse
import io
import os
import logging
import subprocess

from ppci.common import CompilerError, logformat
from ppci import api
from ppci.lang.c import COptions
from ppci.utils.reporting import HtmlReportGenerator
from ppci.format.elf import write_elf


this_dir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("c-test-suite")


def c_test_suite_populate(cls):
    """ Enrich a unittest.TestCase with a function for each test snippet. """
    if "C_TEST_SUITE_DIR" in os.environ:
        c_test_suite_directory = os.path.normpath(
            os.environ["C_TEST_SUITE_DIR"]
        )

        for filename in get_test_snippets(c_test_suite_directory):
            create_test_function(cls, filename)
    else:

        def test_stub(self):
            self.skipTest(
                "Please specify C_TEST_SUITE_DIR for the C test suite"
            )

        setattr(cls, "test_stub", test_stub)
    return cls


def get_test_snippets(c_test_suite_directory, name_filter="*"):
    snippet_folder = os.path.join(
        c_test_suite_directory, "tests", "single-exec"
    )

    # Check if we have a folder:
    if not os.path.isdir(snippet_folder):
        raise ValueError("{} is not a directory".format(snippet_folder))

    for filename in sorted(glob.iglob(os.path.join(snippet_folder, "*.c"))):
        base_name = os.path.splitext(os.path.split(filename)[1])[0]

        if fnmatch.fnmatch(base_name, name_filter):
            yield filename


def create_test_function(cls, filename):
    """ Create a test function for a single snippet """
    snippet_filename = os.path.split(filename)[1]
    test_name = os.path.splitext(snippet_filename)[0]
    test_name = test_name.replace(".", "_").replace("-", "_")
    test_function_name = "test_" + test_name

    def test_function(self):
        perform_test(filename)

    if hasattr(cls, test_function_name):
        raise ValueError("Duplicate test case {}".format(test_function_name))
    setattr(cls, test_function_name, test_function)


def perform_test(filename):
    """ Try to compile the given snippet. """
    logger.info("Step 1: Compile %s!", filename)
    march = "x86_64"

    html_report = os.path.splitext(filename)[0] + "_report.html"

    coptions = COptions()
    libc_include = os.path.join(this_dir, "..", "..", "..", "librt", "libc")
    coptions.add_include_path(libc_include)
    
    # TODO: this should be injected elsewhere?
    coptions.add_define('__LP64__', '1')
    # coptions.enable('freestanding')

    with open(html_report, "w") as rf, HtmlReportGenerator(rf) as reporter:
        with open(filename, "r") as f:
            try:
                obj1 = api.cc(f, march, coptions=coptions, reporter=reporter)
            except CompilerError as ex:
                ex.print()
                raise
    logger.info("Compilation complete, %s", obj1)

    obj0 = api.asm(io.StringIO(STARTERCODE), march)
    obj2 = api.c3c([io.StringIO(BSP_C3_SRC)], [], march)
    with open(os.path.join(libc_include, "lib.c"), "r") as f:
        obj3 = api.cc(f, march, coptions=coptions)

    obj = api.link([obj0, obj1, obj2, obj3], layout=io.StringIO(ARCH_MMAP))

    logger.info("Step 2: Run it!")

    exe_filename = os.path.splitext(filename)[0] + "_executable.elf"
    with open(exe_filename, "wb") as f:
        write_elf(obj, f, type="executable")
    api.chmod_x(exe_filename)

    logger.info("Running %s", exe_filename)
    test_prog = subprocess.Popen(exe_filename, stdout=subprocess.PIPE)
    exit_code = test_prog.wait()
    assert exit_code == 0
    captured_stdout = test_prog.stdout.read().decode("ascii")

    with open(filename + ".expected", "r") as f:
        expected_stdout = f.read()

    # Compare stdout:
    assert captured_stdout == expected_stdout


STARTERCODE = """
global bsp_exit
global bsp_syscall
global main
global start

start:
    call main
    mov rdi, rax
    call bsp_exit

bsp_syscall:
    mov rax, rdi ; abi param 1
    mov rdi, rsi ; abi param 2
    mov rsi, rdx ; abi param 3
    mov rdx, rcx ; abi param 4
    syscall
    ret
"""

ARCH_MMAP = """
ENTRY(start)
MEMORY code LOCATION=0x40000 SIZE=0x10000 {
    SECTION(code)
}
MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
    SECTION(data)
}
"""

BSP_C3_SRC = """
module bsp;

public function void putc(byte c)
{
    syscall(1, 1, cast<int64_t>(&c), 1);
}

public function void exit(int64_t code)
{
    syscall(60, code, 0, 0);
}

function void syscall(int64_t nr, int64_t a, int64_t b, int64_t c);

"""


@c_test_suite_populate
class CTestSuiteTestCase(unittest.TestCase):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument(
        "--folder", help="the folder with the c test suite.",
    )
    parser.add_argument(
        "--filter", help="Apply filtering on the test cases", default="*"
    )
    args = parser.parse_args()

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)

    if args.folder is not None:
        suite_folder = args.folder
    elif "C_TEST_SUITE_DIR" in os.environ:
        suite_folder = os.environ["C_TEST_SUITE_DIR"]
    else:
        parser.print_help()
        print("ERROR: Specify where the c test suite is located!")
        return 1

    for filename in get_test_snippets(suite_folder, name_filter=args.filter):
        perform_test(filename)

    print("OK.")


if __name__ == "__main__":
    main()
