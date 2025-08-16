import io
import math
import unittest

from ppci.common import CompilerError
from ppci.lang.c import CLexer, lexer
from ppci.lang.c.lexer import SourceFile
from ppci.lang.c.options import COptions
from ppci.lang.c.utils import cnum, float_num


class CLexerTestCase(unittest.TestCase):
    """Test the behavior of the lexer"""

    def setUp(self):
        coptions = COptions()
        self.lexer = CLexer(coptions)
        coptions.enable("trigraphs")

    def tokenize(self, src):
        source_file = SourceFile("a.h")
        tokens = list(self.lexer.lex(io.StringIO(src), source_file))
        return tokens

    def test_trigraphs(self):
        """Test the handling of trigraph sequences."""
        src_chunks = [(1, 1, "??( ??) ??/ ??' ??< ??> ??! ??- ??= ")]
        chunks = list(lexer.trigraph_filter(src_chunks))
        # should be: r"[ ] \ ^ { } | ~ #"
        self.assertSequenceEqual(
            [
                (1, 1, "["),
                (1, 4, " "),
                (1, 5, "]"),
                (1, 8, " "),
                (1, 9, "\\"),
                (1, 12, " "),
                (1, 13, "^"),
                (1, 16, " "),
                (1, 17, "{"),
                (1, 20, " "),
                (1, 21, "}"),
                (1, 24, " "),
                (1, 25, "|"),
                (1, 28, " "),
                (1, 29, "~"),
                (1, 32, " "),
                (1, 33, "#"),
                (1, 36, " "),
            ],
            chunks,
        )

    def test_line_glue(self):
        """Test handling of backslash-newline combinations."""
        src_chunks = [
            (1, 1, "bla \\\n"),
            (2, 1, "foo"),
            (2, 5, "baz\\"),
            (2, 8, "\n"),
            (3, 1, "bar"),
            (4, 5, "\\"),
            (4, 8, "\n"),
            (6, 1, "\\"),
        ]
        chunks = list(lexer.continued_lines_filter(src_chunks))
        self.assertSequenceEqual(
            [
                (1, 1, "bla "),
                (2, 1, "foo"),
                (2, 5, "baz"),
                (3, 1, "bar"),
                (6, 1, "\\"),
            ],
            chunks,
        )

    def test_trigraph_challenge(self):
        """Test a nice example for the lexer including some trigraphs"""
        src = "Hell??/\no world"
        tokens = [
            (t.val, t.loc.row, t.loc.col, t.space, t.first)
            for t in self.tokenize(src)
        ]
        self.assertSequenceEqual(
            [("Hello", 1, 1, "", True), ("world", 2, 3, " ", False)], tokens
        )

    def test_block_comment(self):
        """Test block comments"""
        src = "/* bla bla */"
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertEqual([], tokens)

    def test_block_comments_and_values(self):
        src = "1/* bla bla */0/*w00t*/"
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        expected_tokens = [("NUMBER", "1"), ("NUMBER", "0")]
        self.assertEqual(expected_tokens, tokens)

    def test_line_comment(self):
        """Test single line comments"""
        src = """
        int a; // my nice int
        int
        // ?
        b;
        """
        tokens = [(t.typ, t.val, t.loc.row) for t in self.tokenize(src)]
        self.assertSequenceEqual(
            [
                ("BOL", "", 1),
                ("ID", "int", 2),
                ("ID", "a", 2),
                (";", ";", 2),
                # ('BOL', ''),
                ("ID", "int", 3),
                ("BOL", "", 4),
                ("ID", "b", 5),
                (";", ";", 5),
                ("BOL", "", 5),
            ],
            tokens,
        )

    def test_numbers(self):
        src = "212 215u 0xFeeL 073 032U 30l 30ul"
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == "NUMBER" for t in tokens))
        numbers = [cnum(t.val)[0] for t in tokens]
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
        """Test the lexing of the triple dot"""
        # TODO: accept '..' during lexing?
        # giving an error is a safe bet here.
        # the source below could be validly lexed, but does not parse:
        # src = ". .. ... ....."
        src = ". ... ...."
        dots = [t.typ for t in self.tokenize(src)]
        # self.assertSequenceEqual([".", ".", ".", "...", "...", ".", "."],
        #  dots)
        self.assertSequenceEqual([".", "...", "...", "."], dots)

    def test_character_literals(self):
        """Test various character literals"""
        src = r"'a' '\n' L'\0' '\\' '\a' '\b' '\f' '\r' '\t' '\v' '\11' '\xee'"
        expected_tokens = [
            ("CHAR", "'a'"),
            ("CHAR", r"'\n'"),
            ("CHAR", r"L'\0'"),
            ("CHAR", r"'\\'"),
            ("CHAR", r"'\a'"),
            ("CHAR", r"'\b'"),
            ("CHAR", r"'\f'"),
            ("CHAR", r"'\r'"),
            ("CHAR", r"'\t'"),
            ("CHAR", r"'\v'"),
            ("CHAR", r"'\11'"),
            ("CHAR", r"'\xee'"),
        ]
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertSequenceEqual(expected_tokens, tokens)

    def test_string_literals(self):
        """Test various string literals"""
        src = r'"\"|\x7F"'
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        expected_tokens = [("STRING", r'"\"|\x7F"')]
        self.assertSequenceEqual(expected_tokens, tokens)

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

    def test_invalid_suffix(self):
        with self.assertRaises(CompilerError) as cm:
            self.tokenize("0xe+1")
        self.assertEqual(
            "invalid suffix on integer constant", cm.exception.msg
        )

    def test_float_constant(self):
        """Test floating point constant

        See also:
            http://en.cppreference.com/w/c/language/floating_constant
        """
        test_cases = [
            (".12e+2", 12.0),
            (".12e-2", 0.0012),
            ("1.2e3", 1200.0),
            ("12e3", 12000.0),
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
            assert type_spec == ["double"]
            assert isinstance(lexed_val, float)
            assert math.isclose(lexed_val, value)


if __name__ == "__main__":
    unittest.main()
