import unittest
from ppci.api import bf_to_ir, get_arch
from ppci.common import CompilerError


class BrainfuckTestCase(unittest.TestCase):
    def test_bf(self):
        """ Test brainfuck front-end """
        bf_to_ir('.[+>>.<<]', get_arch('example'))

    def test_bf_error(self):
        """ Test if missing backet is detected """
        with self.assertRaises(CompilerError):
            bf_to_ir('.[.>+<][+-[>>]<', 'example')


if __name__ == '__main__':
    unittest.main()
