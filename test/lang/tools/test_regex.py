import unittest
from ppci.lang.tools import regex


class RegexTestCase(unittest.TestCase):
    def test_derivatives(self):
        ab = regex.Symbol("a") + regex.Symbol("b")

        # TODO: work in progress
        print(ab)
        print(ab.derivative("a"))
        print(ab.derivative("b"))
        print(ab.derivative("a").derivative("b"))


class RegexParsingTestCase(unittest.TestCase):
    def test_parse(self):
        re_txt = "[0-9]+"
        expr = regex.parse(re_txt)
        self.assertEqual(
            expr,
            regex.SymbolSet([(48, 57)])
            + regex.Kleene(regex.SymbolSet([(48, 57)])),
        )

    def test_parse_epsilon(self):
        re_txt = ""
        expr = regex.parse(re_txt)
        self.assertEqual(expr, regex.EPSILON)

    def test_parse_a(self):
        re_txt = "a"
        expr = regex.parse(re_txt)
        self.assertEqual(expr, regex.Symbol("a"))

    def test_parse_or(self):
        re_txt = "a|b"
        expr = regex.parse(re_txt)
        self.assertEqual(expr, regex.Symbol("a") | regex.Symbol("b"))


class RegexCompilationTestCase(unittest.TestCase):
    def test_compile(self):
        prog = regex.compile("[0-9]+hi")
        res = list(regex.scan(prog, "1234hi88hi"))
        self.assertEqual(res, ["1234hi", '88hi'])


if __name__ == "__main__":
    unittest.main()
