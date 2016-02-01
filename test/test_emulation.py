import unittest

from ppci.api import construct
from util import relpath, has_qemu, run_qemu


class EmulationTestCase(unittest.TestCase):
    """ Tests the compiler driver """

    def test_m3_bare(self):
        """ Build bare m3 binary and emulate it """
        recipe = relpath('..', 'examples', 'lm3s6965evb', 'build.xml')
        construct(recipe)
        if has_qemu():
            bin_file = relpath('..', 'examples', 'lm3s6965evb', 'bare.bin')
            data = run_qemu(bin_file)
            self.assertEqual('Hello worle', data)

    def test_a9_bare(self):
        """ Build vexpress cortex-A9 binary and emulate it """
        recipe = relpath('..', 'examples', 'realview-pb-a8', 'build.xml')
        construct(recipe)
        if has_qemu():
            bin_file = relpath('..', 'examples', 'realview-pb-a8', 'hello.bin')
            data = run_qemu(bin_file, machine='realview-pb-a8')
            self.assertEqual('Hello worle', data)

    def test_stm32f4_blinky(self):
        """ Compile the example for the stm32f4discovery board """
        recipe = relpath('..', 'examples', 'blinky', 'build.xml')
        construct(recipe)

    def test_msp430_blinky(self):
        recipe = relpath('..', 'examples', 'msp430', 'blinky', 'build.xml')
        construct(recipe)

    def test_arduino(self):
        recipe = relpath('..', 'examples', 'arduino', 'build.xml')
        construct(recipe)

    def test_snake(self):
        """ Compile the snake example """
        recipe = relpath('..', 'examples', 'build.xml')
        construct(recipe)

    def test_linux64_snake(self):
        """ Compile the snake example """
        recipe = relpath('..', 'examples', 'linux64', 'snake', 'build.xml')
        construct(recipe)

    def test_linux64_hello(self):
        """ Compile the hello example for linux64 """
        recipe = relpath('..', 'examples', 'linux64', 'hello', 'build.xml')
        construct(recipe)

if __name__ == '__main__':
    unittest.main()
