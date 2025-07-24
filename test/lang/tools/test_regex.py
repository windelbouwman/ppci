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
            regex.SymbolSet([(48, 57)]) + regex.SymbolSet([(48, 57)]).kleene(),
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

    def test_parse_optional(self):
        re_txt = "a?b"
        expr = regex.parse(re_txt)
        self.assertEqual(
            expr, regex.Symbol("a").optional() + regex.Symbol("b")
        )


class RegexCompilationTestCase(unittest.TestCase):
    def test_compile(self):
        prog = regex.compile("[0-9]+hi")
        print(prog)
        res = list(regex.scan(prog, "1234hi88hi9hi"))
        self.assertEqual(res, ["1234hi", "88hi", "9hi"])

    def wicked_example(self, n):
        """This is an example regex taken from this site:

        https://swtch.com/~rsc/regexp/regexp1.html

        """
        pattern = r"a?" * n + "a" * n
        prog = regex.compile(pattern)
        print(prog)
        res = list(regex.scan(prog, "a" * n))
        self.assertEqual(res, ["a" * n])

    def test_performance_example_n1(self):
        self.wicked_example(1)

    def test_performance_example_n2(self):
        self.wicked_example(2)

    def test_performance_example_n3(self):
        self.wicked_example(3)

    def test_scanner(self):
        # Idea for scanner creation:
        tokens = {
            "identifier": "[a-z]+",
            "space": " +",
            "operator": r"[=\-\+]",
            "number": "[0-9]+",
        }
        scanner = regex.make_scanner(tokens)
        text = "bla = 99 + fu- 1"
        tokens = list(scanner.scan(text))
        self.assertEqual(
            tokens,
            [
                ("identifier", "bla"),
                ("space", " "),
                ("operator", "="),
                ("space", " "),
                ("number", "99"),
                ("space", " "),
                ("operator", "+"),
                ("space", " "),
                ("identifier", "fu"),
                ("operator", "-"),
                ("space", " "),
                ("number", "1"),
            ],
        )

    def test_examples(self):
        for pattern, text, is_found in re_cases:
            print("Test pattern", pattern, "with text", text)
            prog = regex.compile(pattern)
            print("compiled regex", prog)
            try:
                res = list(regex.scan(prog, text))
            except ValueError:
                self.assertFalse(is_found)
            else:
                self.assertTrue(is_found)
                print(res)
                self.assertEqual(res, list(is_found))


# From cpython re_tests.py file some examples:
re_cases = [
    (r"abc", "abc", ("abc",)),
    (r"abc", "xbc", False),
    (r"abc", "axc", False),
    (r"abc", "abx", False),
    (r"ab*c", "abc", ("abc",)),
    (r"ab*bc", "abc", ("abc",)),
    (r"ab*bc", "abbc", ("abbc",)),
    (r"ab*bc", "abbbbc", ("abbbbc",)),
    (r"ab+bc", "abc", False),
    (r"ab+bc", "abq", False),
    (r"ab+bc", "abbc", ("abbc",)),
    (r"ab+bc", "abbbbc", ("abbbbc",)),
    (r"ab?bc", "abbc", ("abbc",)),
    (r"ab?bc", "abc", ("abc",)),
    (r"ab?bc", "abbbbc", False),
    (r"ab?c", "abc", ("abc",)),
    (r"ab?c", "ac", ("ac",)),
    (r"a.c", "abc", ("abc",)),
    (r"a.c", "axc", ("axc",)),
    (r"a.*c", "axyzc", ("axyzc",)),
    (r"a.*c", "axyzd", False),
    (r"a[bc]d", "abd", ("abd",)),
    (r"a[bc]d", "acd", ("acd",)),
    (r"a[bc]d", "axd", False),
    (r"a[b-d]e", "ace", ("ace",)),
]

if __name__ == "__main__":
    unittest.main()
