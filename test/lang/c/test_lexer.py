import io
import math
import unittest

from ppci.common import CompilerError
from ppci.lang.c import CLexer, lexer
from ppci.lang.c.lexer import SourceFile
from ppci.lang.c.options import COptions
from ppci.lang.c.utils import cnum, float_num


class CLexerTestCase(unittest.TestCase):
    """ Test the behavior of the lexer """

    def setUp(self):
        coptions = COptions()
        self.lexer = CLexer(coptions)
        coptions.enable("trigraphs")

    def tokenize(self, src):
        source_file = SourceFile("a.h")
        tokens = list(self.lexer.lex(io.StringIO(src), source_file))
        return tokens

    def test_generate_characters(self):
        src = "ab\ndf"
        source_file = SourceFile("a.h")
        chars = list(lexer.create_characters(io.StringIO(src), source_file))
        self.assertSequenceEqual([1, 1, 1, 2, 2], [c.loc.row for c in chars])
        self.assertSequenceEqual([1, 2, 3, 1, 2], [c.loc.col for c in chars])

    def test_trigraphs(self):
        src = "??( ??) ??/ ??' ??< ??> ??! ??- ??="
        source_file = SourceFile("a.h")
        chars = list(lexer.create_characters(io.StringIO(src), source_file))
        chars = list(lexer.trigraph_filter(chars))
        self.assertSequenceEqual(
            list(r"[ ] \ ^ { } | ~ #"), [c.char for c in chars]
        )
        self.assertSequenceEqual([1] * 17, [c.loc.row for c in chars])
        self.assertSequenceEqual(
            [1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21, 24, 25, 28, 29, 32, 33],
            [c.loc.col for c in chars],
        )

    def test_trigraph_challenge(self):
        """ Test a nice example for the lexer including some trigraphs """
        src = "Hell??/\no world"
        tokens = self.tokenize(src)
        self.assertSequenceEqual(["Hello", "world"], [t.val for t in tokens])
        self.assertSequenceEqual([1, 2], [t.loc.row for t in tokens])
        self.assertSequenceEqual([1, 3], [t.loc.col for t in tokens])
        self.assertSequenceEqual(["", " "], [t.space for t in tokens])
        self.assertSequenceEqual([True, False], [t.first for t in tokens])

    def test_block_comment(self):
        """ Test block comments """
        src = "/* bla bla */"
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertEqual([], tokens)

    def test_block_comments_and_values(self):
        src = "1/* bla bla */0/*w00t*/"
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertEqual([("NUMBER", "1"), ("NUMBER", "0")], tokens)

    def test_line_comment(self):
        """ Test single line comments """
        src = """
        int a; // my nice int
        int
        // ?
        b;
        """
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertSequenceEqual(
            [
                ("BOL", ""),
                ("ID", "int"),
                ("ID", "a"),
                (";", ";"),
                # ('BOL', ''),
                ("ID", "int"),
                ("BOL", ""),
                ("ID", "b"),
                (";", ";"),
                ("BOL", ""),
            ],
            tokens,
        )

    def test_numbers(self):
        src = "212 215u 0xFeeL 073 032U 30l 30ul"
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == "NUMBER" for t in tokens))
        numbers = list(map(lambda t: cnum(t.val)[0], tokens))
        self.assertSequenceEqual([212, 215, 4078, 59, 26, 30, 30], numbers)

    def test_assignment_operators(self):
        operators = [
            "+=",
            "-=",
            "*=",
            "/=",
            "%=",
            "|=",
            "<<=",
            ">>=",
            "&=",
            "^=",
            "~=",
        ]
        src = " ".join(operators)
        tokens = self.tokenize(src)
        lexed_values = [t.val for t in tokens]
        self.assertSequenceEqual(operators, lexed_values)

    def test_dotdotdot(self):
        """ Test the lexing of the triple dot """
        src = ". .. ... ....."
        tokens = self.tokenize(src)
        dots = list(map(lambda t: t.typ, tokens))
        self.assertSequenceEqual([".", ".", ".", "...", "...", ".", "."], dots)

    def test_character_literals(self):
        """ Test various character literals """
        src = r"'a' '\n' L'\0' '\\' '\a' '\b' '\f' '\r' '\t' '\v' '\11' '\xee'"
        expected_chars = [
            "'a'",
            r"'\n'",
            r"L'\0'",
            r"'\\'",
            r"'\a'",
            r"'\b'",
            r"'\f'",
            r"'\r'",
            r"'\t'",
            r"'\v'",
            r"'\11'",
            r"'\xee'",
        ]
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == "CHAR" for t in tokens))
        chars = list(map(lambda t: t.val, tokens))
        self.assertSequenceEqual(expected_chars, chars)

    def test_string_literals(self):
        """ Test various string literals """
        src = r'"\"|\x7F"'
        tokens = self.tokenize(src)

        expected_types = ["STRING"]
        types = list(map(lambda t: t.typ, tokens))
        self.assertSequenceEqual(expected_types, types)

        expected_strings = [r'"\"|\x7F"']
        strings = list(map(lambda t: t.val, tokens))
        self.assertSequenceEqual(expected_strings, strings)

    def test_token_spacing(self):
        src = "1239hello"
        # TODO: should this raise an error?
        self.tokenize(src)

    def test_lexical_error(self):
        src = "'asfdfd'"
        # TODO: should this raise an error?
        with self.assertRaises(CompilerError) as cm:
            self.tokenize(src)
        self.assertEqual("Expected '", cm.exception.msg)

    def test_float_constant(self):
        """ Test floating point constant

        See also:
            http://en.cppreference.com/w/c/language/floating_constant
        """
        test_cases = [
            (".12e+2", 12.0),
            (".12e-2", 0.0012),
            ('1.2e3', 1200.0),
            ('12e3', 12000.0),
            ("3.14", 3.14),
            ("1.", 1.0),
            (".1", 0.1),
            ("0.7", 0.7),
        ]
        for src, value in test_cases:
            # print(src)
            tokens = self.tokenize(src)
            self.assertEqual(1, len(tokens))
            self.assertEqual("FLOAT", tokens[0].typ)
            self.assertEqual(src, tokens[0].val)
            lexed_val, type_spec = float_num(tokens[0].val)
            assert type_spec == ['double']
            assert isinstance(lexed_val, float)
            assert math.isclose(lexed_val, value)


if __name__ == "__main__":
    unittest.main()
