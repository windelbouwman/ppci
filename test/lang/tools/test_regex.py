import unittest
from ppci.lang.tools import regex


class RegexTestCase(unittest.TestCase):
    def test_derivatives(self):
        ab = regex.Symbol('a') + regex.Symbol('b')

        # TODO: work in progress
        print(ab)
        print(ab.derivative('a'))
        print(ab.derivative('b'))
        print(ab.derivative('a').derivative('b'))

    def test_parse(self):
        re_txt = '[0-9]+'
        regex.parse(re_txt)


class SymbolSetTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
