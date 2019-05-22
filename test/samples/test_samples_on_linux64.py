import unittest
import io
import os
import platform
import subprocess
from tempfile import mkstemp

from sample_helpers import add_samples, build
from util import do_long_tests, make_filename

from ppci.api import asm, link, objcopy


@unittest.skipUnless(do_long_tests('x86_64'), 'skipping slow tests')
@add_samples('simple', 'medium', 'hard', '8bit', 'fp', 'double')
class TestSamplesOnX86Linux(unittest.TestCase):
    opt_level = 0
    march = "x86_64"
    startercode = """
    section reset

    global bsp_putc
    global main_main

    start:
        call main_main
        call bsp_exit

    bsp_putc:
            mov [0x20000000], rdi ; store char passed in rdi

            mov rax, 1 ; 1=sys_write
            mov rdi, 1 ; file descriptor
            mov rsi, char_to_print ; char* buf
            mov rdx, 1 ; count
            syscall
            ret

    bsp_exit:
            mov rax, 60
            mov rdi, 0
            syscall
            ret

    section data
        char_to_print:
        dd 0
        dd 0
    """
    arch_mmap = """
    MEMORY code LOCATION=0x40000 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
        SECTION(data)
    }
    """
    bsp_c3_src = """
    module bsp;
    public function void putc(byte c);
    // function void exit();
    """

    def do(self, src, expected_output, lang='c3'):
        bsp_c3 = io.StringIO(self.bsp_c3_src)
        startercode = io.StringIO(self.startercode)
        base_filename = make_filename(self.id())
        obj = build(
            base_filename, src, bsp_c3, startercode, self.march,
            self.opt_level, io.StringIO(self.arch_mmap),
            lang=lang, bin_format='elf')

        exe = base_filename + '.elf'

        if has_linux():
            if hasattr(subprocess, 'TimeoutExpired'):
                res = subprocess.check_output(exe, timeout=10)
            else:
                res = subprocess.check_output(exe)
            res = res.decode('ascii')
            self.assertEqual(expected_output, res)


class TestSamplesOnX86LinuxO2(TestSamplesOnX86Linux):
    opt_level = 2


def has_linux():
    return platform.machine() == 'x86_64' and platform.system() == 'Linux'


@unittest.skipIf(not has_linux(), 'no 64 bit linux found')
class LinuxTests(unittest.TestCase):
    """ Run tests against the linux syscall api """

    def test_exit42(self):
        """
            ; exit with code 42:
            ; syscall 60 = exit, rax is first argument, rdi second
        """
        src = io.StringIO("""
            section code
            mov rax, 60
            mov rdi, 42
            syscall
            """)
        mmap = """
        MEMORY code LOCATION=0x40000 SIZE=0x10000 {
            SECTION(code)
        }
        """
        obj = asm(src, 'x86_64')
        handle, exe = mkstemp()
        os.close(handle)
        obj2 = link([obj], layout=io.StringIO(mmap))
        objcopy(obj2, 'prog', 'elf', exe)
        if hasattr(subprocess, 'TimeoutExpired'):
            returncode = subprocess.call(exe, timeout=10)
        else:
            returncode = subprocess.call(exe)
        self.assertEqual(42, returncode)
