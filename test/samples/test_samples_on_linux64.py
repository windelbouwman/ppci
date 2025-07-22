import unittest
import io
import os
import platform
import subprocess
from tempfile import mkstemp

from .sample_helpers import add_samples, build
from ..helper_util import do_long_tests, make_filename

from ppci.api import asm, link, objcopy


@unittest.skipUnless(do_long_tests("x86_64"), "skipping slow tests")
@add_samples("simple", "medium", "hard", "8bit", "fp", "double")
class TestSamplesOnX86Linux(unittest.TestCase):
    opt_level = 0
    march = "x86_64"

    def do(self, src, expected_output, lang="c3"):
        bsp_c3 = io.StringIO(BSP_C3_SRC)
        base_filename = make_filename(self.id())
        build(
            base_filename,
            src,
            bsp_c3,
            io.StringIO(STARTERCODE),
            self.march,
            self.opt_level,
            io.StringIO(ARCH_MMAP),
            lang=lang,
            bin_format="elf",
        )

        exe = base_filename + ".elf"

        if has_linux():
            if hasattr(subprocess, "TimeoutExpired"):
                res = subprocess.check_output(exe, timeout=10)
            else:
                res = subprocess.check_output(exe)
            res = res.decode("ascii")
            self.assertEqual(expected_output, res)


class TestSamplesOnX86LinuxO2(TestSamplesOnX86Linux):
    opt_level = 2


STARTERCODE = """
global bsp_exit
global bsp_syscall
global main_main
global start

start:
    call main_main
    call bsp_exit

bsp_syscall:
    mov rax, rdi ; abi param 1
    mov rdi, rsi ; abi param 2
    mov rsi, rdx ; abi param 3
    mov rdx, rcx ; abi param 4
    ; mov eax, edi ; abi param 1
    ; mov edi, esi ; abi param 2
    ; mov esi, edx ; abi param 3
    ; mov edx, ecx ; abi param 4
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

public function void exit()
{
    syscall(60, 0, 0, 0);
}

function void syscall(int64_t nr, int64_t a, int64_t b, int64_t c);

"""


def has_linux():
    return platform.machine() == "x86_64" and platform.system() == "Linux"


@unittest.skipIf(not has_linux(), "no 64 bit linux found")
class LinuxTests(unittest.TestCase):
    """ Run tests against the linux syscall api """

    def test_exit42(self):
        """
            ; exit with code 42:
            ; syscall 60 = exit, rax is first argument, rdi second
        """
        src = io.StringIO(
            """
            section code
            global start
            start:
            mov rax, 60
            mov rdi, 42
            syscall
            """
        )
        mmap = """
        ENTRY(start)
        MEMORY code LOCATION=0x40000 SIZE=0x10000 {
            SECTION(code)
        }
        """
        obj = asm(src, "x86_64")
        handle, exe = mkstemp()
        os.close(handle)
        obj2 = link([obj], layout=io.StringIO(mmap))
        objcopy(obj2, "prog", "elf", exe)
        if hasattr(subprocess, "TimeoutExpired"):
            returncode = subprocess.call(exe, timeout=10)
        else:
            returncode = subprocess.call(exe)
        self.assertEqual(42, returncode)
