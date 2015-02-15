import unittest

from ppci.buildfunctions import construct
from ppci.target import target_list
from util import relpath, has_qemu, run_qemu


class EmulationTestCase(unittest.TestCase):
    """ Tests the compiler driver """

    def test_m3_bare(self):
        """ Build bare m3 binary and emulate it """
        recipe = relpath('data', 'lm3s6965evb', 'build.xml')
        self.assertEqual(0, construct(recipe))
        if not has_qemu():
            self.skipTest('Not running Qemu test')
        data = run_qemu(relpath('data', 'lm3s6965evb', 'bare.bin'))
        self.assertEqual('Hello worle', data)

    def test_a9_bare(self):
        """ Build vexpress cortex-A9 binary and emulate it """
        recipe = relpath('data', 'realview-pb-a8', 'build.xml')
        self.assertEqual(0, construct(recipe))
        if not has_qemu():
            self.skipTest('Not running Qemu test')
        data = run_qemu(relpath('data', 'realview-pb-a8', 'hello.bin'),
                        machine='realview-pb-a8')
        self.assertEqual('Hello worle', data)

    def test_burn2(self):
        """ Compile the example for the stm32f4discovery board """
        recipe = relpath('data', 'stm32f4xx', 'build.xml')
        self.assertEqual(0, construct(recipe))

    # @unittest.skip('A real world example, hence contains errors :)')
    def test_snake(self):
        """ Compile the snake example """
        recipe = relpath('..', 'examples', 'build.xml')
        self.assertEqual(0, construct(recipe))

if __name__ == '__main__':
    unittest.main()
