import unittest
from ppci.api import bf2ir
from ppci.arch.example import SimpleTarget
from ppci.common import CompilerError


class BrainfuckTestCase(unittest.TestCase):
    def test_bf(self):
        """ Test brainfuck front-end """
        bf2ir('.[+>>.<<]', SimpleTarget())

    def test_bf_error(self):
        """ Test if missing backet is detected """
        with self.assertRaises(CompilerError):
            bf2ir('.[.>+<][+-[>>]<', SimpleTarget())
