
import unittest
import io
import os
from ppci.buildfunctions import bfcompile
from testemulation import runQemu, has_qemu, relpath
from ppci.buildfunctions import assemble, c3compile, link, objcopy


class testBrainfuckBuilder(unittest.TestCase):
    def setUp(self):
        if not has_qemu():
            self.skipTest('Not running qemu tests')

    def testHelloWorld(self):
        """ Test brainfuck program """
        hello_world = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
        res = self.do(hello_world)
        self.assertEqual("Hello world!\n", res)

    def do(self, src):
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
        obj = bfcompile(src, 'arm')
        o2 = c3compile([
            relpath('data', 'realview-pb-a8', 'arch.c3'),
            ], [], march)
        o3 = link([o2, o1, obj], io.StringIO(arch_mmap), march)

        sample_filename = 'testsample.bin'
        objcopy(o3, 'image', 'bin', sample_filename)

        # Run bin file in emulator:
        # Somehow vexpress-a9 and realview-pb-a8 differ?
        res = runQemu(sample_filename, machine='realview-pb-a8')
        os.remove(sample_filename)
        return res

if __name__ == '__main__':
    unittest.main()
