import unittest
import io
import logging
import re
import os
import platform
import subprocess
from tempfile import mkstemp

from sample_helpers import add_samples
from util import has_qemu, qemu, relpath, run_python, source_files
from util import has_iverilog, run_msp430, run_picorv32
from util import has_avr_emulator, run_avr, run_nodejs
from util import do_long_tests, do_iverilog, make_filename

from ppci.api import asm, c3c, link, objcopy, bfcompile, cc, get_current_arch
from ppci.api import c3_to_ir, bf_to_ir, ir_to_python, optimize, c_to_ir
from ppci.utils.reporting import HtmlReportGenerator
from ppci.utils import uboot_image
from ppci.binutils.objectfile import merge_memories
from ppci.lang.c import COptions


def enable_report_logger(filename):
    logging.getLogger().setLevel(logging.DEBUG)
    fh = logging.StreamHandler(filename)
    logging.getLogger().addHandler(fh)


def only_bf(txt):
    """ Strip a string from all characters, except brainfuck chars """
    return re.sub(r'[^\.,<>\+-\]\[]', '', txt)


@add_samples('32bit')
class I32Samples:
    """ 32-bit samples """

    @unittest.skip('too large codesize')
    def test_brain_fuck_hello_world(self):
        """ Test brainfuck hello world program """
        hello_world = """++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>
        .>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."""
        self.do(hello_world, "Hello World!\n", lang='bf')

    @unittest.skip('too slow test')
    def test_brain_fuck_quine(self):
        """ A quine is a program that outputs itself! """
        quine = """>>+>>+++++>>++>>+++>>+>>++++++>>++>>++>>++>>+++++>>+>>++++>>
        +>>+++>>+>>+>>++>>++>>+>>+>>+>>+++>>+>>++++++>>+++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++>>+>>++>>++
        +++++>>+++++++++++++++++++>>++++>>+>>++>>+>>+++++>>+>>++++>>
        +>>+++>>+>>+++++++>>+>>++>>+>>++++++>>+>>+++>>+>>+++++>>+>>+
        +++>>+>>++++++>>+>>+++>>+>>+++++>>+>>++++>>+>>++>>+>>+>>+>>+
        ++>>+>>++++++>>+++>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>+++
        +>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>++++>>+>>++++++
        >>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>+
        +>>+++++++++++++++++++++++++++++++++++++++++++++++++>>+>>+>>
        +++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>++>>+>>+
        ++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>+++
        +>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>
        >+++++>>+>>++>>+++++++++++++++++++++++++++++++++++++++++++++
        ++++++++++++++++++++++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++++
        >>++>>+>>++++++>>++++>>+++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>
        >+>>++>>+>>+++++>>+>>+++>>+>>++++>>+>>++++++>>+>>++>>+>>++++
        +>>+>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>++>>+++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++++>>+>>+>>+
        ++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>++>>+>>++
        +++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>++++
        >>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>>
        +++++>>+>>++>>++++++++++++++++++++++++++++++++++++++++++++++
        ++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++++>>++>>+>>++++++>>+++
        +>>+++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>
        >+++>>+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>
        >++>>+++>>+>>+++++>>+>>++>>+++++++++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        >>+>>+>>+++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>
        ++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++
        >>+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>
        >+++>>+>>+++++>>+>>++>>+++++++++++++++++++++++++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++>>+
        >>+>>+++>>+>>++++>>+>>++++++>>+++++>>++>>+>>++++++>>++++>>++
        +>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>
        >+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>
        +++>>+>>+++++>>+>>++>>++++++++++++++++++++++++++++++++++++++
        ++++++++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++
        >>++>>++>>++>>+++++>>+>>++++>>++>>++>>+>>+++++++>>++>>+++>>+
        >>++++++>>++++>>++>>+>>++++++[<<]>>[[-<+>>+<]+++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++..-----------
        -------->[-<.>]<[-]<[->+<]>>>]<<[-<+>[<-]>[>]<<[>+++++++++++
        ++++++++++++++++++++++++++++++++++++++<-]<<<]>>>>[-<+>[<-]>[
        >]<<[>++++++++++++++++++++++++++++++++++++++++++++++++++++++
        +++++++++++++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>+++++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++<-]<<<]>>>>[-
        <+>[<-]>[>]<<[>+++++++++++++++++++++++++++++++++++++++++++++
        +++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>+++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        ++++++<-]<<<]>>>>[-<+>[<-]>[>]<<[>++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        ++++++++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>++++++++++++++++++++++
        ++++++++++++++++++++++++<-]<<<]>>[[->>.<<]>>>>]"""
        self.do(quine, only_bf(quine), lang='bf')


class BuildMixin:
    opt_level = 0

    def build(self, src, lang='c3', bin_format=None,
              elf_format=None, code_image='code'):
        """ Construct object file from source snippet """
        base_filename = make_filename(self.id())

        startercode = io.StringIO(self.startercode)
        if hasattr(self, 'bsp_c3_src'):
            bsp_c3 = io.StringIO(getattr(self, 'bsp_c3_src'))
        else:
            bsp_c3 = self.bsp_c3

        obj = build(
            base_filename, src, bsp_c3, startercode, self.march,
            self.opt_level,
            io.StringIO(self.arch_mmap), lang=lang, bin_format=bin_format,
            elf_format=elf_format, code_image=code_image)

        return obj, base_filename




@unittest.skipUnless(do_long_tests('x86_64'), 'skipping slow tests')
@add_samples('simple', 'medium', 'hard', '8bit', 'fp', 'double')
class TestSamplesOnX86Linux(unittest.TestCase, BuildMixin):
    march = "x86_64"
    startercode = """
    section reset

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
        obj, base_filename = self.build(src, lang, bin_format='elf')
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


if __name__ == '__main__':
    with open('sample_report.log', 'w') as report_file:
        enable_report_logger(report_file)
        unittest.main()
