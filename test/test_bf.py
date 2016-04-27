import unittest
from ppci.api import bf2ir, get_arch
from ppci.common import CompilerError


class BrainfuckTestCase(unittest.TestCase):
    def test_bf(self):
        """ Test brainfuck front-end """
        bf2ir('.[+>>.<<]', get_arch('example'))

    def test_bf_error(self):
        """ Test if missing backet is detected """
        with self.assertRaises(CompilerError):
            bf2ir('.[.>+<][+-[>>]<', 'example')


if __name__ == '__main__':
    unittest.main()
