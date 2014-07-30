import unittest
import os
import io
from testemulation import runQemu, has_qemu
from testzcc import relpath
from ppci.buildfunctions import assemble, c3compile, link

mod_io_src = """
module io;
import arch;

function void println(string txt)
{
    print(txt);
    arch.putc(10); // Newline!
}

function void print(string txt)
{
    var int i;
    i = 0;

    while (i < txt->len)
    {
        arch.putc(cast<int>(txt->txt[i]));
        i = i + 1;
    }
}

// Print integer in hexadecimal notation:
function void print_int(int i)
{
    print("0x");

    // int txt[20];
    var int b;
    var int c;

    for (b=28; b >= 0; b = b - 4)
    {
        c = (i >> b) & 0xF;
        if (c < 10)
        {
            arch.putc( 48 + c );
        }
        else
        {
            arch.putc( 65 - 10 + c );
        }
    }

    arch.putc(10); // Newline!
}

function void print2(string label, int value)
{
    print(label);
    print_int(value);
}
"""


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
         var int G;
         function void do1()
         {
            G = G + 1;
            io.print2("G=", G);
         }
         function void do5()
         {
            G = G + 5;
            io.print2("G=", G);
         }
         function void start()
         {
            G = 0;
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
        startercode = """
        section reset
        mov sp, 0x30000   ; setup stack pointer
        BL sample_start     ; Branch to sample start
        local_loop:
        B local_loop
        """

        modarchcode = """
        module arch;

        function void putc(int c)
        {
            var int *UART0DR;
            UART0DR = cast<int*>(0x10009000); // UART0 DR register
            *UART0DR = c;
        }

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
        o1 = assemble(io.StringIO(startercode), 'arm')
        o2 = c3compile([
            relpath('..', 'kernel', 'src', 'io.c3'),
            io.StringIO(modarchcode),
            io.StringIO(src)], [], 'arm')
        o3 = link([o2, o1], io.StringIO(arch_mmap), 'arm')

        img_data = o3.get_image('image')
        sample_filename = 'testsample.bin'
        with open(sample_filename, 'wb') as f:
            f.write(img_data)

        # Check bin file exists:
        self.assertTrue(os.path.isfile(sample_filename))

        # Run bin file in emulator:
        res = runQemu(sample_filename, machine='vexpress-a9')
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

        img_data = o3.get_image('image')
        sample_filename = 'testsample.bin'
        with open(sample_filename, 'wb') as f:
            f.write(img_data)

        # Check bin file exists:
        self.assertTrue(os.path.isfile(sample_filename))

        # Run bin file in emulator:
        res = runQemu(sample_filename, machine='vexpress-a9')
        os.remove(sample_filename)
        self.assertEqual(expected_output, res)

# TODO: test samples on thumb target..


if __name__ == '__main__':
    unittest.main()

