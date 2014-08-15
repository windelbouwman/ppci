import unittest
import os
import io
import logging
from util import runQemu, has_qemu, relpath
from ppci.buildfunctions import assemble, c3compile, link, objcopy
from ppci.report import RstFormatter


def enable_report_logger(filename):
    logging.getLogger().setLevel(logging.DEBUG)
    fh = logging.StreamHandler(filename)
    fh.setFormatter(RstFormatter())
    logging.getLogger().addHandler(fh)


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


class TestSamplesOnVexpress(unittest.TestCase, Samples):
    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def do(self, src, expected_output):
        march = "arm"
        startercode = """
        section reset
        mov sp, 0x30000   ; setup stack pointer
        BL sample_start     ; Branch to sample start
        local_loop:
        B local_loop
        """

        arch_mmap = """
        MEMORY image LOCATION=0x10000 SIZE=0x10000 {
            SECTION(reset)
            SECTION(code)
        }

        MEMORY ram LOCATION=0x20000 SIZE=0x10000 {
            SECTION(data)
        }
        """
        # Construct binary file from snippet:
        o1 = assemble(io.StringIO(startercode), march)
        o2 = c3compile([
            relpath('data', 'io.c3'),
            relpath('data', 'realview-pb-a8', 'arch.c3'),
            io.StringIO(src)], [], march)
        o3 = link([o2, o1], io.StringIO(arch_mmap), march)

        sample_filename = 'testsample.bin'
        objcopy(o3, 'image', 'bin', sample_filename)

        # Run bin file in emulator:
        # Somehow vexpress-a9 and realview-pb-a8 differ?
        res = runQemu(sample_filename, machine='realview-pb-a8')
        os.remove(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnCortexM3(unittest.TestCase, Samples):
    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def do(self, src, expected_output, lang="c3"):
        march = "thumb"
        startercode = """
        section reset
        dcd 0x20000678
        dcd 0x00000009
        BL sample_start     ; Branch to sample start
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
        o2 = c3compile([
            relpath('data', 'io.c3'),
            relpath('data', 'lm3s6965evb', 'arch.c3'),
            io.StringIO(src)], [], march)
        o3 = link([o2, o1], io.StringIO(arch_mmap), march)

        sample_filename = 'testsample.bin'
        objcopy(o3, 'code', 'bin', sample_filename)

        # Run bin file in emulator:
        res = runQemu(sample_filename, machine='lm3s811evb')
        os.remove(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnX86(unittest.TestCase, Samples):
    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')
        self.skipTest('No x86 target yet')

    def do(self, src, expected_output):
        # Construct binary file from snippet:
        o1 = assemble(io.StringIO(startercode), 'x86')
        o2 = c3compile([
            relpath('..', 'kernel', 'src', 'io.c3'),
            io.StringIO(modarchcode),
            io.StringIO(src)], [], 'x86')
        o3 = link([o2, o1], io.StringIO(arch_mmap), 'x86')

        sample_filename = 'testsample.bin'
        objcopy(o3, 'image', 'bin', sample_filename)

        # Check bin file exists:
        self.assertTrue(os.path.isfile(sample_filename))

        # Run bin file in emulator:
        res = runQemu(sample_filename, machine='vexpress-a9')
        os.remove(sample_filename)
        self.assertEqual(expected_output, res)

# TODO: test samples on thumb target..


if __name__ == '__main__':
    with open('sample_report.log', 'w') as report_file:
        enable_report_logger(report_file)
        unittest.main()
