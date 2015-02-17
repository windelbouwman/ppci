import unittest
import io
import logging
import re
import string
import os
from util import run_qemu, has_qemu, relpath, run_python
from ppci.buildfunctions import assemble, c3compile, link, objcopy, bfcompile
from ppci.buildfunctions import c3toir, bf2ir, ir_to_python
try:
    from ppci.utils.stlink import stlink_run_sram_and_trace
except ImportError:
    stlink_run_sram_and_trace = None
from ppci.report import RstFormatter
from ppci.ir2py import IrToPython


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
    fh.setFormatter(RstFormatter())
    logging.getLogger().addHandler(fh)


def only_bf(txt):
    """ Strip a string from all characters, except brainfuck chars """
    return re.sub('[^\.,<>\+-\]\[]', '', txt)


class Samples:

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

    def test_for_loop_print(self):
        snippet = """
         module sample;
         import io;
         function void start()
         {
            var int i;
            var int b;
            b = 2;
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
         }
        """
        res = "tftf"
        self.do(snippet, res)

    def test_if_statement(self):
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

    def testBrainFuckSierPinski(self):
        """ Test sierpinski triangle """
        code = """
                                        >
                                       + +
                                      +   +
                                     [ < + +
                                    +       +
                                   + +     + +
                                  >   -   ]   >
                                 + + + + + + + +
                                [               >
                               + +             + +
                              <   -           ]   >
                             > + + >         > > + >
                            >       >       +       <
                           < <     < <     < <     < <
                          <   [   -   [   -   >   +   <
                         ] > [ - < + > > > . < < ] > > >
                        [                               [
                       - >                             + +
                      +   +                           +   +
                     + + [ >                         + + + +
                    <       -                       ]       >
                   . <     < [                     - >     + <
                  ]   +   >   [                   -   >   +   +
                 + + + + + + + +                 < < + > ] > . [
                -               ]               >               ]
               ] +             < <             < [             - [
              -   >           +   <           ]   +           >   [
             - < + >         > > - [         - > + <         ] + + >
            [       -       <       -       >       ]       <       <
           < ]     < <     < <     ] +     + +     + +     + +     + +
          +   .   +   +   +   .   [   -   ]   <   ]   +   +   +   +   +
        """
        sier = "                                *    \n"
        sier += "\r                               * *    \n"
        sier += "\r                              *   *    \n"
        sier += "\r                             * * * *    \n"
        sier += "\r                            *       *    \n"
        sier += "\r                           * *     * *    \n"
        sier += "\r                          *   *   *   *    \n"
        sier += "\r                         * * * * * * * *    \n"
        sier += "\r                        *               *    \n"
        sier += "\r                       * *             * *    \n"
        sier += "\r                      *   *           *   *    \n"
        sier += "\r                     * * * *         * * * *    \n"
        sier += "\r                    *       *       *       *    \n"
        sier += "\r                   * *     * *     * *     * *    \n"
        sier += "\r                  *   *   *   *   *   *   *   *    \n"
        sier += "\r                 * * * * * * * * * * * * * * * *    \n"
        sier += "\r                *                               *    \n"
        sier += "\r               * *                             * *    \n"
        sier += "\r              *   *                           *   *    \n"
        sier += "\r             * * * *                         * * * *    \n"
        sier += "\r            *       *                       *       *    \n"
        sier += "\r           * *     * *                     * *     * *    \n"
        sier += "\r          *   *   *   *                   *   *   *   *    \n"
        sier += "\r         * * * * * * * *                 * * * * * * * *    \n"
        sier += "\r        *               *               *               *    \n"
        sier += "\r       * *             * *             * *             * *    \n"
        sier += "\r      *   *           *   *           *   *           *   *    \n"
        sier += "\r     * * * *         * * * *         * * * *         * * * *    \n"
        sier += "\r    *       *       *       *       *       *       *       *    \n"
        sier += "\r   * *     * *     * *     * *     * *     * *     * *     * *    \n"
        sier += "\r  *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *    \n"
        sier += "\r * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *    \n\r"
        self.do(code, sier, lang='bf')

    @unittest.skip('not working')
    def testBrainFuckBottlesOfBeer(self):
        """ Test bottles of beer song text """
        hello_world = """
        >>>>>++++++++[<+++++++++>-]<+[>>[>]+[<]<-]>++++++++++[<+++++
        +++++>-]<[>>[+>]<[<]<-]<++++++++[>++++++++[>>->->->>>>>>>>>>
        >->>>->>>>>>->->->->>->>>->>>>->>>>>->->>>>>>->>>>->>>>>->->
        >>>>->>>->>>>>>>->-[<]<-]>>++>++>->>+>++>++>+>>>>++>>->+>>->
        >>>++>>+>+>+>--->>->+>+>->++>>>->++>>+>+>+>--->>-->>+>>->+>+
        >>->>+>++>+>+>->+>>++>++>->>++>->>++>+>++>+>>+>---[<]<<-]>>>
        ++++>++++>+++>--->++>->->->>[-]>->-->[-]>+++>++>+>+++>--->>>
        --->[-]>+>+>+>--->[-]>+++>++>+>+++>->+++>>+++>++>---->->->+>
        --->[-]>->---->-->>+++>++>+>>+++>->++>++>+>->+++>+++>---->--
        >-->+++>++++>->+++>---->--->++>>+>->->---[[<]<]+++++++++[<+<
        +++++++++++>>-]<<[>>>>>[<]>[.>]>--[>.>]<[<<]>++>>>[.>]>[>]>[
        .>]<[[<]<]>>[.>]>--[>.>]<[<<]>++>>>[.>]>[.>]>[>]>[.>]<[[<]<]
        <<[<]>>>+<[>-]>[>]<[+++++++++[<+<->>>>>+<<<-]+<<[>>-]>>>[<]<
        <<++++++++++>>[>>[-]+<<-]>>-<<]>>>-[>]>-<<[<]>[.>]>--[>.>]<[
        <<]>++>>>[.>]>[>]>[.>]<.[[<]<]<<[<]>>-<-]
        """
        # Construct beer song:
        couplettes = []
        for n in range(99, 2, -1):
            couplet = "{0} bottles of beer on the wall.\n".format(n, n-1)
            couplet += "{0} bottles of beer...\n".format(n, n-1)
            couplet += "Take one down, pass it around,\n"
            couplet += "{1} bottles of beer on the wall.\n".format(n, n-1)
            couplettes.append(couplet)
        couplet = "2 bottles of beer on the wall.\n2 bottles of beer...\n"
        couplet += "Take one down, pass it around,\n"
        couplet += "1 bottle of beer on the wall.\n"
        couplettes.append(couplet)
        couplet = "1 bottle of beer on the wall.\n1 bottle of beer...\n"
        couplet += "Take one down, pass it around,\n"
        couplet += "0 bottles of beer on the wall.\n"
        couplettes.append(couplet)
        song_text = '\n'.join(couplettes) + '\n'
        self.do(hello_world, song_text, lang='bf')


class DoMixin:
    def do(self, src, expected_output, lang="c3"):
        """ Generic do function """
        march = self.march
        startercode = self.startercode
        arch_mmap = self.arch_mmap
        arch_c3 = self.arch_c3

        # Determine base names:
        base_filename = make_filename(self.id())
        list_filename = base_filename + '.lst'
        sample_filename = base_filename + '.bin'

        # Open listings file:
        lst_file = open(list_filename, 'w')

        # Construct binary file from snippet:
        o1 = assemble(io.StringIO(startercode), march)
        if lang == 'c3':
            o2 = c3compile([
                relpath('data', 'io.c3'),
                arch_c3,
                io.StringIO(src)], [], march, lst_file=lst_file)
            o3 = link([o2, o1], io.StringIO(arch_mmap), march)
        elif lang == 'bf':
            obj = bfcompile(src, march, lst_file=lst_file)
            o2 = c3compile([
                arch_c3
                ], [], march, lst_file=lst_file)
            o3 = link([o2, o1, obj], io.StringIO(arch_mmap), march)
        else:
            raise Exception('language not implemented')

        objcopy(o3, 'code', 'bin', sample_filename)
        lst_file.close()

        # Run bin file in emulator:
        res = self.run_sample(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnVexpress(unittest.TestCase, Samples, DoMixin):
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
    MEMORY code LOCATION=0x10000 SIZE=0x10000 {
        SECTION(reset)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000 SIZE=0xA0000 {
        SECTION(data)
    }
    """
    arch_c3 = relpath('data', 'realview-pb-a8', 'arch.c3')

    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def run_sample(self, sample_filename):
        # Run bin file in emulator:
        dump_file = sample_filename.split('.')[0] + '.dump'
        return run_qemu(
            sample_filename, machine='realview-pb-a8',
            dump_file=dump_file, dump_range=(0x20000, 0xf0000))


class TestSamplesOnCortexM3(unittest.TestCase, Samples, DoMixin):
    """ The lm3s811 has 64 k memory """
    def setUp(self):
        # self.skipTest('Tests got broken!')
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    march = "thumb"
    startercode = """
    section reset
    dcd 0x2000f000
    dcd 0x00000009
    BL sample_start     ; Branch to sample start
    BL arch_exit  ; do exit stuff
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
    arch_c3 = relpath('data', 'lm3s6965evb', 'arch.c3')

    def run_sample(self, sample_filename):
        # Run bin file in emulator:
        dump_file = sample_filename.split('.')[0] + '.dump'
        return run_qemu(
            sample_filename, machine='lm3s6965evb', # lm3s811evb
            dump_file=dump_file, dump_range=(0x20000000, 0x20010000))


class TestSamplesOnSTM32F407(unittest.TestCase, Samples, DoMixin):
    """
        The stm32f4 discovery board has the following memory:
        0x2001 c000 - 0x2001 ffff SRAM2
        0x2000 0000 - 0x2001 bfff SRAM1

        For the test samples we choose the following scheme:
        0x2000 0000 - 0x2000 1000 -> code  [4 k]
        0x2000 1000 - 0x2000 2000 -> stack [4 k]
        0x2000 2000 - 0x2001 ffff -> data  [120 k]
    """
    def setUp(self):
        if stlink_run_sram_and_trace is None:
            self.skipTest('stlink not loaded')

    march = "thumb"
    startercode = """
    section reset
    BL sample_start     ; Branch to sample start
    BL arch_exit  ; do exit stuff
    local_loop:
    B local_loop
    """

    arch_mmap = """
    MEMORY code LOCATION=0x20000000 SIZE=0x1000
    {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }

    MEMORY ram LOCATION=0x20002000 SIZE=0x1E000
    {
        SECTION(data)
    }
    """
    arch_c3 = relpath('data', 'stm32f4xx', 'arch.c3')

    def run_sample(self, sample_filename):
        # Run bin file in emulator:
        # res = run_qemu(sample_filename, machine='lm3s811evb')
        # self.assertEqual(expected_output, res)
        self.skipTest('Not functional yet')
        with open(sample_filename, 'rb') as f:
            image = f.read()
        out = io.StringIO()
        stlink_run_sram_and_trace(image, output=out)
        return out.getvalue()


class TestSamplesOnPython(unittest.TestCase, Samples):
    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        sample_filename = base_filename + '.py'

        if lang == 'c3':
            ir_mods = list(c3toir([
                relpath('data', 'io.c3'),
                relpath('data', 'lm3s6965evb', 'arch.c3'),
                io.StringIO(src)], [], "arm"))
        elif lang == 'bf':
            ir_mods = [bf2ir(src)]

        with open(sample_filename, 'w') as f:
            i2p = IrToPython()
            i2p.f = f
            i2p.header()
            for m in ir_mods:
                ir_to_python(m, f)
            # Add glue:
            print('', file=f)
            print('def arch_putc(c):', file=f)
            print('    print(chr(c), end="")', file=f)
            print('sample_start()', file=f)
        res = run_python(sample_filename)
        self.assertEqual(expected_output, res)


if __name__ == '__main__':
    with open('sample_report.log', 'w') as report_file:
        enable_report_logger(report_file)
        unittest.main()
