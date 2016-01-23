import unittest
import io
import logging
import re
import string
import os
import platform
import subprocess
from tempfile import mkstemp
from util import run_qemu, has_qemu, relpath, run_python
from ppci.api import asm, c3c, link, objcopy, bfcompile
from ppci.api import c3toir, bf2ir, ir_to_python
from ppci.utils.reporting import HtmlReportGenerator, complete_report


def make_filename(s):
    """ Remove all invalid characters from a string for a valid filename.
        And create a directory if none present.
    """
    output_dir = relpath('listings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    valid_chars = string.ascii_letters + string.digits
    basename = ''.join(c for c in s if c in valid_chars)
    return os.path.join(output_dir, basename)


def enable_report_logger(filename):
    logging.getLogger().setLevel(logging.DEBUG)
    fh = logging.StreamHandler(filename)
    logging.getLogger().addHandler(fh)


def only_bf(txt):
    """ Strip a string from all characters, except brainfuck chars """
    return re.sub('[^\.,<>\+-\]\[]', '', txt)


class SimpleSamples:
    """ Collection of snippets with expected output """
    def test_print(self):
        """ Test if print statement works """
        snippet = """
         module sample;
         import io;
         function void start()
         {
            io.print("Hello world");
         }
        """
        self.do(snippet, "Hello world")

    def test_if_statement(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i = 13;
            if (i*7 < 100)
            {
                io.print("Wow");
            }
            else
            {
                io.print("Outch");
            }
         }
        """
        res = "Wow"
        self.do(snippet, res)

    def test_boolean_exotics(self):
        """ Test boolean use in different ways """
        snippet = """
         module sample;
         import io;
         function void print_bool(bool v)
         {
            if (v)
            {
                io.print("t");
            }
            else
            {
                io.print("f");
            }
         }

         function bool no()
         {
            return false;
         }

         var int key;

         function bool getkey(int* k)
         {
            if (key == 0)
            {
                *k = 1;
            }
            else
            {
                return false;
            }

            return true;
         }

         function void start()
         {
            var bool tv;
            print_bool(true);
            print_bool(no());
            tv = no() or 1 == 1;
            print_bool(tv);
            key = 1;
            var int k;
            print_bool(getkey(&k) and true);
            print_bool(not no());
         }
        """
        res = "tftft"
        self.do(snippet, res)


class I32Samples:
    """ 32-bit samples """

    def test_for_loop_print(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i;
            var int b = 2;
            for (i=0; i<10; i = i + 1)
            {
              io.print2("A = ", i);
              b *= i + 1;
            }
            io.print2("B = ", b);
         }
        """
        res = "".join("A = 0x{0:08X}\n".format(a) for a in range(10))
        res += "B = 0x006EBE00\n"
        self.do(snippet, res)

    def test_c3_quine(self):
        """ Quine in the c3 language """
        src = """module sample;import io;import bsp;function void start(){var string x="module sample;import io;import bsp;function void start(){var string x=;io.print_sub(x,0,70);bsp.putc(34);io.print(x);bsp.putc(34);io.print_sub(x,70,154);}";io.print_sub(x,0,70);bsp.putc(34);io.print(x);bsp.putc(34);io.print_sub(x,70,154);}"""
        self.do(src, src)

    @unittest.skip('actually tests qemu pipe, not ppci')
    def test_large_for_loop_print(self):
        """ This test actually tests the qemu pipe system """
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i;
            for (i=0; i<10000; i = i + 1)
            {
              io.print2("A = ", i);
            }
         }
        """
        res = "".join("A = 0x{0:08X}\n".format(a) for a in range(10000))
        self.do(snippet, res)

    def test_bug1(self):
        """ Strange bug was found here """
        snippet = """
         module sample;
         var int x;
         function void start()
         {
            var int i = 0;
            if (x != i)
            {
            }
         }
        """
        res = ""
        self.do(snippet, res)

    def test_bug2(self):
        """ Test pointer arithmatic """
        snippet = """
         module sample;
         var int* x;
         function void start()
         {
            var int i;
            x = 10;
            x += 15;
            i = cast<int>(x);
         }
        """
        res = ""
        self.do(snippet, res)

    def test_bug3(self):
        """ Apparently function arguments get sorted by name??? """
        snippet = """
         module sample;
         import io;
         var int b;
         function void cpy(byte* dst, byte* src, int size)
         {
            io.print2("to=", cast<int>(dst));
            io.print2("from=", cast<int>(src));
            io.print2("size=", size);
         }
         function void start()
         {
            var byte[4] data;
            data[0] = 4;
            data[1] = 3;
            data[2] = 0;
            data[3] = 0;
            var byte* image_ptr = &data[0];
            var int x = *cast<int*>(image_ptr);
            io.print2("x=", x);
            cpy(1, 2, x);
         }
        """
        res = "x=0x00000304\nto=0x00000001\nfrom=0x00000002\nsize=0x00000304\n"
        self.do(snippet, res)

    def test_complex_variables(self):
        """ Test local variables of complex type """
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int[10] x;
            var int[10] y;
            y[1] = 0x11;
            y[2] = 0x33;
            x[1] = 0x44;
            x[2] = 0x55;
            io.print2("y[1]=", y[1]);
            io.print2("x[1]=", x[1]);
         }
        """
        res = "y[1]=0x00000011\nx[1]=0x00000044\n"
        self.do(snippet, res)

    def test_parameter_passing4(self):
        """ Check that parameter passing works as expected """
        snippet = """
         module sample;
         import io;
         function void dump(int a, int b, int c, int d)
         {
            io.print2("a=", a);
            io.print2("b=", b);
            io.print2("c=", c);
            io.print2("d=", d);
         }
         function void dump2(int a, int b, int c, int d)
         {
            dump(a,b,c,d);
         }
         function void start()
         {
            dump(4,55,66,0x1337);
            dump2(4,55,66,0x1337);
         }
        """
        res = "a=0x{0:08X}\n".format(4)
        res += "b=0x{0:08X}\n".format(55)
        res += "c=0x{0:08X}\n".format(66)
        res += "d=0x{0:08X}\n".format(0x1337)
        res = res + res
        self.do(snippet, res)

    def test_pointer_fu(self):
        """ Check if 8 bits pointer assignments work with 32 bit pointers.
            This test is architecture dependent!
            Assume little endianess.
        """
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int w;
            var int* pw;
            var byte* pb;
            var byte* pb2;
            var byte** ppb;
            pw = &w;
            pb = cast<byte*>(pw);
            pb2 = pb + 2;
            *pw = 0x11223344;
            *pb = 0x88;
            ppb = &pb2;
            **ppb = 0x66; // double pointer hackzzz
            io.print2("w=", w);
         }
        """
        self.do(snippet, "w=0x11663388\n")

    def test_arithmatic_operations(self):
        """
            Check arithmatics
        """
        snippet = """
         module sample;
         import io;
         var int x;
         function void set_x(int v)
         {
            x = v;
         }

         var int d;

         function void start()
         {
            var int w;
            d = 2;
            set_x(13);
            w = x / d;
            io.print2("w=", w);

            w = x - d;
            io.print2("w=", w);

            w = x % d;
            io.print2("w=", w);

            w = x + d;
            io.print2("w=", w);

            w = x ^ 0xf;
            io.print2("w=", w);
         }
        """
        self.do(snippet, "w=0x00000006\nw=0x0000000B\nw=0x00000001\nw=0x0000000F\nw=0x00000002\n")

    def test_global_variable(self):
        snippet = """
         module sample;
         import io;
         var int MyGlob;
         var struct {int a; int b;}[10] cplx1;
         var struct {int a; int b;}[10] cplx2;
         function void do1()
         {
            MyGlob = MyGlob + 1;
            io.print2("G=", MyGlob);
         }

         function void do5()
         {
            MyGlob = MyGlob + 5;
            io.print2("G=", MyGlob);
         }

         function int* get_ptr()
         {
            return &MyGlob;
         }

         function void start()
         {
            MyGlob = 0;
            do1();
            do1();
            do5();
            do1();
            do5();
            *(get_ptr()) += 2;
            *(get_ptr()) += 8;
            do5();
            cplx1[1].b = 2;
            cplx2[1].a = 22;
            io.print2("cplx1 1 b =", cplx1[1].b);
            io.print2("cplx2 1 a =", cplx2[1].a);
         }
        """
        res = "".join("G=0x{0:08X}\n".format(a) for a in [1, 2, 7, 8, 13, 28])
        res += "cplx1 1 b =0x00000002\n"
        res += "cplx2 1 a =0x00000016\n"
        self.do(snippet, res)

    def test_const(self):
        snippet = """
         module sample;
         import io;
         const int a = 1;
         const int b = a + 6;
         function void start()
         {
            io.print2("a=", a);
            io.print2("b=", b);
         }
        """
        res = "a=0x{0:08X}\nb=0x{1:08X}\n".format(1, 7)
        self.do(snippet, res)

    def test_fibo(self):
        """ Test recursive function with fibonacci algorithm """
        snippet = """
         module sample;
         import io;
         function int fib(int x)
         {
            if (x < 3)
            {
                return 1;
            }
            else
            {
                return fib(x - 1) + fib(x - 2);
            }
         }

         function void start()
         {
            var int i;
            i = fib(13);
            io.print2("fib(13)=", i);
         }
        """
        # fib(13) == 233 == 0xe9
        res = "fib(13)=0x000000E9\n"
        self.do(snippet, res)

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
    def build(self, src, lang='c3', bin_format='bin'):
        base_filename = make_filename(self.id())
        list_filename = base_filename + '.html'

        startercode = self.startercode
        report_generator = HtmlReportGenerator(open(list_filename, 'w'))
        if hasattr(self, 'bsp_c3_src'):
            bsp_c3 = io.StringIO(getattr(self, 'bsp_c3_src'))
        else:
            bsp_c3 = self.bsp_c3

        with complete_report(report_generator) as reporter:
            o1 = asm(io.StringIO(startercode), self.march)
            if lang == 'c3':
                o2 = c3c([
                    relpath('..', 'librt', 'io.c3'),
                    bsp_c3,
                    io.StringIO(src)], [], self.march, reporter=reporter)
                objs = [o1, o2]
            elif lang == 'bf':
                o3 = bfcompile(src, self.march, reporter=reporter)
                o2 = c3c(
                    [bsp_c3], [], self.march, reporter=reporter)
                objs = [o1, o2, o3]
            else:
                raise Exception('language not implemented')
            obj = link(
                objs,
                io.StringIO(self.arch_mmap),
                self.march, use_runtime=True, reporter=reporter)

        # Determine base names:
        sample_filename = make_filename(self.id()) + '.' + bin_format
        objcopy(obj, 'code', bin_format, sample_filename)
        return sample_filename


class TestSamplesOnVexpress(
        unittest.TestCase, SimpleSamples, I32Samples, BuildMixin):
    maxDiff = None
    march = "arm"
    startercode = """
    section reset
    mov sp, 0xF0000   ; setup stack pointer
    BL sample_start     ; Branch to sample start
    BL bsp_exit  ; do exit stuff
    local_loop:
    B local_loop
    """
    arch_mmap = """
    MEMORY code LOCATION=0x10000 SIZE=0x10000 {
        SECTION(reset)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000 SIZE=0xA0000 {
        SECTION(data)
    }
    """
    bsp_c3 = relpath('..', 'examples', 'realview-pb-a8', 'arch.c3')

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        sample_filename = self.build(src, lang)

        # Run bin file in emulator:
        if has_qemu():
            res = run_qemu(sample_filename, machine='realview-pb-a8')
            self.assertEqual(expected_output, res)


class TestSamplesOnCortexM3(
        unittest.TestCase, SimpleSamples, I32Samples, BuildMixin):
    """ The lm3s811 has 64 k memory """

    march = "thumb"
    startercode = """
    section reset
    dd 0x2000f000
    dd 0x00000009
    BL sample_start     ; Branch to sample start
    BL bsp_exit  ; do exit stuff
    local_loop:
    B local_loop
    """
    arch_mmap = """
    MEMORY code LOCATION=0x0 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
        SECTION(data)
    }
    """
    bsp_c3 = relpath('..', 'examples', 'lm3s6965evb', 'arch.c3')

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        sample_filename = self.build(src, lang)

        # Run bin file in emulator:
        if has_qemu():
            res = run_qemu(sample_filename, machine='lm3s6965evb')
            # lm3s811evb
            self.assertEqual(expected_output, res)


class TestSamplesOnPython(unittest.TestCase, SimpleSamples, I32Samples):
    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        sample_filename = base_filename + '.py'
        list_filename = base_filename + '.html'

        report_generator = HtmlReportGenerator(open(list_filename, 'w'))
        with complete_report(report_generator) as reporter:
            if lang == 'c3':
                ir_modules = list(c3toir([
                    relpath('..', 'librt', 'io.c3'),
                    relpath('..', 'examples', 'lm3s6965evb', 'arch.c3'),
                    io.StringIO(src)], [], "arm", reporter=reporter))
            elif lang == 'bf':
                ir_modules = [bf2ir(src, 'arm')]

            with open(sample_filename, 'w') as f:
                ir_to_python(ir_modules, f, reporter=reporter)
        res = run_python(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnMsp430(unittest.TestCase, SimpleSamples, BuildMixin):
    march = "msp430"
    startercode = """
    section reset
    """
    arch_mmap = """
    MEMORY code LOCATION=0x0 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000000 SIZE=0xA000 { SECTION(data) }
    """
    bsp_c3_src = """
    module bsp;

    public function void putc(byte c)
    {
    }

    function void exit()
    {
        putc(4); // End of transmission
    }
    """

    def do(self, src, expected_output, lang='c3'):
        self.build(src, lang)


class TestSamplesOnAvr(unittest.TestCase, SimpleSamples, BuildMixin):
    march = "avr"
    startercode = """
    section reset
    """
    arch_mmap = """
        MEMORY code LOCATION=0x0 SIZE=0x8000 {  SECTION(code) }
        MEMORY ram LOCATION=0x100 SIZE=0x800 {  SECTION(data) }
        """
    bsp_c3_src = """
    module bsp;
    public function void putc(byte c)
    {
    }

    function void exit()
    {
        putc(4); // End of transmission
    }
    """

    def do(self, src, expected_output, lang='c3'):
        self.build(src, lang)


class TestSamplesOnX86Linux(unittest.TestCase, SimpleSamples, BuildMixin):
    march = "x86_64"
    startercode = """
    section reset

    start:
        call sample_start
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
    function void exit();
    """

    def do(self, src, expected_output, lang='c3'):
        exe = self.build(src, lang, bin_format='elf')
        if has_linux():
            if hasattr(subprocess, 'TimeoutExpired'):
                res = subprocess.check_output(exe, timeout=10)
            else:
                res = subprocess.check_output(exe)
            res = res.decode('ascii')
            self.assertEqual(expected_output, res)


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
        obj2 = link([obj], io.StringIO(mmap), 'x86_64')
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
