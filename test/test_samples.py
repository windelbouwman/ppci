import unittest
import io
import logging
import re
from util import run_qemu, has_qemu, relpath, tryrm, run_python
from ppci.buildfunctions import assemble, c3compile, link, objcopy, bfcompile
from ppci.buildfunctions import c3toir, bf2ir, ir_to_python
from ppci.report import RstFormatter


def enable_report_logger(filename):
    logging.getLogger().setLevel(logging.DEBUG)
    fh = logging.StreamHandler(filename)
    fh.setFormatter(RstFormatter())
    logging.getLogger().addHandler(fh)


def only_bf(txt):
    """ Strip a string from all characters, except brainfuck chars """
    return re.sub('[^\.,<>\+-\]\[]', '', txt)

class Samples:
    def testPrint(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            io.print("Hello world");
         }
        """
        self.do(snippet, "Hello world")

    def testForLoopPrint(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i;
            for (i=0; i<10; i = i + 1)
            {
              io.print2("A = ", i);
            }
         }
        """
        res = "".join("A = 0x{0:08X}\n".format(a) for a in range(10))
        self.do(snippet, res)

    def testIfStatement(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i;
            i = 13;
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

    def testParameterPassing4(self):
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
         function void start()
         {
            dump(4,55,66,0x1337);
         }
        """
        res = "a=0x{0:08X}\n".format(4)
        res += "b=0x{0:08X}\n".format(55)
        res += "c=0x{0:08X}\n".format(66)
        res += "d=0x{0:08X}\n".format(0x1337)
        self.do(snippet, res)

    def testGlobalVariable(self):
        snippet = """
         module sample;
         import io;
         var int MyGlob;
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
         function void start()
         {
            MyGlob = 0;
            do1();
            do1();
            do5();
            do1();
            do5();
         }
        """
        res = "".join("G=0x{0:08X}\n".format(a) for a in [1, 2, 7, 8, 13])
        self.do(snippet, res)

    def testConst(self):
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

    def testFibo(self):
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

    def testBrainFuckHelloWorld(self):
        """ Test brainfuck hello world program """
        hello_world = """++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>
        .>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."""
        self.do(hello_world, "Hello World!\n", lang='bf')

    @unittest.skip('Too slow')
    def testBrainFuckQuine(self):
        """ A quine is a program that outputs itself! """
        quine1 = """->+>+++>>+>++>+>+++>>+>++>>>+>+>+>++>+>>>>+++>+>>++
        >+>+++>>++>
        ++>>+>>+>++>++>+>>>>+++>+>>>>++>++>>>>+>>++>+>+++>>>++>>++++
        ++>>+>>++>+>>>>+++>>+++++>>+>+++>>>++>>++>>+>>++>+>+++>>>++>
        >+++++++++++++>>+>>++>+>+++>+>+++>>>++>>++++>>+>>++>+>>>>+++
        >>+++++>>>>++>>>>+>+>++>>+++>+>>>>+++>+>>>>+++>+>>>>+++>>++>
        ++>+>+++>+>++>++>>>>>>++>+>+++>>>>>+++>>>++>+>+++>+>+>++>>>>
        >>++>>>+>>>++>+>>>>+++>+>>>+>>++>+>++++++++++++++++++>>>>+>+
        >>>+>>++>+>+++>>>++>>++++++++>>+>>++>+>>>>+++>>++++++>>>+>++
        >>+++>+>+>++>+>+++>>>>>+++>>>+>+>>++>+>+++>>>++>>++++++++>>+
        >>++>+>>>>+++>>++++>>+>+++>>>>>>++>+>+++>>+>++>>>>+>+>++>+>>
        >>+++>>+++>>>+[[->>+<<]<+]+++++[->+++++++++<]>.[+]>>[<<+++++
        ++[->+++++++++<]>-.------------------->-[-<.<+>>]<[+]<+>>>]<
        <<[-[-[-[>>+<++++++[->+++++<]]>++++++++++++++<]>+++<]++++++[
        ->+++++++<]>+<<<-[->>>++<<<]>[->>.<<]<<]"""

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


class TestSamplesOnVexpress(unittest.TestCase, Samples):
    sample_filename = 'testsample.bin'

    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def tearDown(self):
        tryrm(self.sample_filename)

    def do(self, src, expected_output, lang='c3'):
        march = "arm"
        startercode = """
        section reset
        mov sp, 0xF0000   ; setup stack pointer
        BL sample_start     ; Branch to sample start
        BL arch_exit  ; do exit stuff
        local_loop:
        B local_loop
        """

        arch_mmap = """
        MEMORY image LOCATION=0x10000 SIZE=0x10000 {
            SECTION(reset)
            SECTION(code)
        }

        MEMORY ram LOCATION=0x20000 SIZE=0xA0000 {
            SECTION(data)
        }
        """
        # Construct binary file from snippet:
        o1 = assemble(io.StringIO(startercode), march)
        if lang == 'c3':
            o2 = c3compile([
                relpath('data', 'io.c3'),
                relpath('data', 'realview-pb-a8', 'arch.c3'),
                io.StringIO(src)], [], march)
            o3 = link([o2, o1], io.StringIO(arch_mmap), march)
        elif lang == 'bf':
            obj = bfcompile(src, march)
            o2 = c3compile([
                relpath('data', 'realview-pb-a8', 'arch.c3')
                ], [], march)
            o3 = link([o2, o1, obj], io.StringIO(arch_mmap), march)
        else:
            raise Exception('language not implemented')

        objcopy(o3, 'image', 'bin', self.sample_filename)

        # Run bin file in emulator:
        # Somehow vexpress-a9 and realview-pb-a8 differ?
        res = run_qemu(self.sample_filename, machine='realview-pb-a8')
        self.assertEqual(expected_output, res)


class TestSamplesOnCortexM3(unittest.TestCase, Samples):
    sample_filename = 'testsample.bin'

    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def tearDown(self):
        tryrm(self.sample_filename)

    def do(self, src, expected_output, lang="c3"):
        march = "thumb"
        startercode = """
        section reset
        dcd 0x20000900
        dcd 0x00000009
        BL sample_start     ; Branch to sample start
        BL arch_exit  ; do exit stuff
        local_loop:
        B local_loop
        """

        arch_mmap = """
        MEMORY code LOCATION=0x10000 SIZE=0x10000 {
            SECTION(reset)
            ALIGN(4)
            SECTION(code)
        }

        MEMORY ram LOCATION=0x20000000 SIZE=0x100 {
            SECTION(data)
        }
        """
        # Construct binary file from snippet:
        o1 = assemble(io.StringIO(startercode), march)
        if lang == 'c3':
            o2 = c3compile([
                relpath('data', 'io.c3'),
                relpath('data', 'lm3s6965evb', 'arch.c3'),
                io.StringIO(src)], [], march)
            o3 = link([o2, o1], io.StringIO(arch_mmap), march)
        elif lang == 'bf':
            obj = bfcompile(src, march)
            o2 = c3compile([
                relpath('data', 'lm3s6965evb', 'arch.c3')
                ], [], march)
            o3 = link([o2, o1, obj], io.StringIO(arch_mmap), march)
        else:
            raise Exception('language not implemented')

        objcopy(o3, 'code', 'bin', self.sample_filename)

        # Run bin file in emulator:
        res = run_qemu(self.sample_filename, machine='lm3s811evb')
        self.assertEqual(expected_output, res)


class TestSamplesOnPython(unittest.TestCase, Samples):
    sample_filename = 'generated_code.py'

    def setUp(self):
        pass

    def do(self, src, expected_output, lang='c3'):
        if lang == 'c3':
            ir_mods = list(c3toir([
                relpath('data', 'io.c3'),
                relpath('data', 'lm3s6965evb', 'arch.c3'),
                io.StringIO(src)], [], "arm"))
        elif lang == 'bf':
            ir_mods = [bf2ir(src)]

        with open(self.sample_filename, 'w') as f:
            print('mem = list()', file=f)
            for m in ir_mods:
                ir_to_python(m, f)
            # Add glue:
            print('', file=f)
            print('def arch_putc(c):', file=f)
            print('    print(chr(c), end="")', file=f)
            print('sample_start()', file=f)
        res = run_python(self.sample_filename)
        self.assertEqual(expected_output, res)


if __name__ == '__main__':
    with open('sample_report.log', 'w') as report_file:
        enable_report_logger(report_file)
        unittest.main()
