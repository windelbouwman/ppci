import unittest
import io
import os
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, CPreProcessor, CLexer, lexer, CParser, nodes
from ppci.lang.c.preprocessor import CTokenPrinter
from ppci.lang.c.options import COptions
from ppci.lang.c.castxml import CastXmlReader
from ppci.lang.c.utils import cnum
from ppci.arch.example import ExampleArch
from ppci import ir
from ppci.irutils import Verifier


testdir = os.path.dirname(os.path.abspath(__file__))


def relpath(*args):
    return os.path.normpath(os.path.join(testdir, *args))


class CLexerTestCase(unittest.TestCase):
    """ Test the behavior of the lexer """
    def setUp(self):
        coptions = COptions()
        self.lexer = CLexer(coptions)
        coptions.enable('trigraphs')

    def tokenize(self, src):
        tokens = list(self.lexer.lex(io.StringIO(src), 'a.h'))
        return tokens

    def test_generate_characters(self):
        src = "ab\ndf"
        chars = list(lexer.create_characters(io.StringIO(src), 'a.h'))
        self.assertSequenceEqual([1, 1, 1, 2, 2], [c.loc.row for c in chars])
        self.assertSequenceEqual([1, 2, 3, 1, 2], [c.loc.col for c in chars])

    def test_trigraphs(self):
        src = "??( ??) ??/ ??' ??< ??> ??! ??- ??="
        chars = list(lexer.create_characters(io.StringIO(src), 'a.h'))
        chars = list(lexer.trigraph_filter(chars))
        self.assertSequenceEqual(
            list(r'[ ] \ ^ { } | ~ #'), [c.char for c in chars])
        self.assertSequenceEqual([1] * 17, [c.loc.row for c in chars])
        self.assertSequenceEqual(
            [1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21, 24, 25, 28, 29, 32, 33],
            [c.loc.col for c in chars])

    def test_trigraph_challenge(self):
        """ Test a nice example for the lexer including some trigraphs """
        src = "Hell??/\no world"
        tokens = self.tokenize(src)
        self.assertSequenceEqual(['Hello', 'world'], [t.val for t in tokens])
        self.assertSequenceEqual([1, 2], [t.loc.row for t in tokens])
        self.assertSequenceEqual([1, 3], [t.loc.col for t in tokens])
        self.assertSequenceEqual(['', ' '], [t.space for t in tokens])
        self.assertSequenceEqual([True, False], [t.first for t in tokens])

    def test_block_comment(self):
        src = "/* bla bla */"
        tokens = self.tokenize(src)

    def test_numbers(self):
        src = "212 215u 0xFeeL 073 032U 30l 30ul"
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == 'NUMBER' for t in tokens))
        numbers = list(map(lambda t: cnum(t.val), tokens))
        self.assertSequenceEqual([212, 215, 4078, 59, 26, 30, 30], numbers)

    def test_character_literals(self):
        src = r"'a' '\n' L'\0'"
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == 'CHAR' for t in tokens))
        chars = list(map(lambda t: t.val, tokens))
        self.assertSequenceEqual(["'a'", r"'\n'", r"L'\0'"], chars)

    def test_token_spacing(self):
        src = "1239hello"
        # TODO: should this raise an error?
        tokens = self.tokenize(src)


class CPreProcessorTestCase(unittest.TestCase):
    """ Test the preprocessor functioning """
    def setUp(self):
        self.preprocessor = CPreProcessor(COptions())

    def preprocess(self, src, expected=None):
        f = io.StringIO(src)
        lines = self.preprocessor.process(f, 'dummy.t')

        f2 = io.StringIO()
        CTokenPrinter().dump(lines, file=f2)
        actual_output = f2.getvalue()
        if expected:
            self.assertEqual(expected, actual_output)

    def test_empty(self):
        """ Test the obvious empty case! """
        self.preprocess('', '')

    def test_simple_define(self):
        src = r"""
        #define A 100
        printf("%i\n",A);"""
        expected = r"""# 1 "dummy.t"


        printf("%i\n",100);"""
        self.preprocess(src, expected)

    def test_recursive_define(self):
        src = r"""
        #define A(X,Y) (100 + X + (Y))
        A(A(1,2),A(A(23,G),22))"""
        expected = r"""# 1 "dummy.t"


        (100 + (100 + 1 + (2)) + ((100 + (100 + 23 + (G)) + (22))))"""
        self.preprocess(src, expected)

    def test_if_expression(self):
        src = r"""#if L'\0'-1 > 0
        unsigned wide char
        #endif
        end"""
        expected = r"""# 1 "dummy.t"


        end"""
        self.preprocess(src, expected)

    def test_ifdef(self):
        src = r"""
        #ifdef A
        printf("%i\n", A);
        #else
        printf("%i\n", 100);
        #endif"""
        expected = r"""# 1 "dummy.t"



        printf("%i\n", 100);
"""
        self.preprocess(src, expected)

    def test_line_directive(self):
        src = r"""
        #line 1234 "cpp"
        __LINE__; __FILE__;
        #line 567
        __LINE__; __FILE__;
        """
        expected = r"""# 1 "dummy.t"

        1234; "cpp";
        567; "cpp";"""
        # TODO: check expected output
        self.preprocess(src)

    def test_error_directive(self):
        src = r"""
        #error this is not yet implemented 1234 #&!*^"""
        with self.assertRaises(CompilerError) as cm:
            self.preprocess(src)
        self.assertEqual(2, cm.exception.loc.row)
        self.assertEqual(
            'this is not yet implemented 1234 #&!*^', cm.exception.msg)

    def test_intermediate_example(self):
        """ Check a medium hard example """
        src = r"""
        int X = A;

        int B = 5;
        #define A 100 + B
        #define B 55 + B
        #define D defined(A) && defined B A
        #if defined C || defined(A) && defined B
        int X=0;
        #else
        int Y=0;
        #endif

        D

        #define G 56
        #if G == 2 + 54
        int g = G;
        #endif

        int defined = 2;
        int main()
        {
        printf("%i\n", A);
        }"""
        expected = r"""# 1 "dummy.t"

        int X = A;

        int B = 5;




        int X=0;



        defined(100 + 55 + B) && defined 55 + B 100 + 55 + B



        int g = 56;


        int defined = 2;
        int main()
        {
        printf("%i\n", 100 + 55 + B);
        }"""
        self.preprocess(src, expected)

    def test_hard_example(self):
        """ Check a hard example """
        src = r"""
        #define A(B,C) 100 + B + # C
        #define B 55 + B ## ghe
        #define D(x,y) x ## _ ## y
        #define E 100 + B ## woei

        A(2,3)
        B
        A(5,abc - 23)
        D(wa,ttuh)
        E"""
        expected = r"""# 1 "dummy.t"






        100 + 2 + "3"
        55 + Bghe
        100 + 5 + "abc - 23"
        wa_ttuh
        100 + Bwoei"""
        self.preprocess(src, expected)

    def test_scandalous_hack_1(self):
        """ Test a scandalous use of the preprocessor """
        src = r"""#define function() 123
        #define concat(a,b) a ## b
        concat(func,tion)()"""
        expected = r"""# 1 "dummy.t"


        123"""
        self.preprocess(src, expected)

    def test_cpplib_example(self):
        """ Test a nested function like macro on multiple lines """
        src = r"""#define foo(x) bar x
        foo(foo
        ) (2)"""
        expected = r"""# 1 "dummy.t"

        bar foo (2)"""
        self.preprocess(src, expected)

    def test_elif(self):
        """ Test elif with else """
        src = r"""#define __WORDSIZE 32
        #if __WORDSIZE == 32
        int32
        #elif __WORDSIZE == 64
        int64
        #else
        int999
        #endif"""
        expected = r"""# 1 "dummy.t"


        int32


"""
        self.preprocess(src, expected)

    def test_mismatching_endif(self):
        src = r"""     #endif   """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_mismatching_else(self):
        src = r"""     #else   """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_double_else(self):
        src = r""" #ifdef A
        #else
        #else
        """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_non_terminated_if_stack(self):
        src = r"""#ifdef B
        #ifdef A
        #else
        #endif
        """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_command_structure(self):
        src = r"""
        #define COMMAND(NAME)  { #NAME, NAME ## _command }
        struct command commands[] =
        {
          COMMAND(quit),
          COMMAND(help),
        };"""
        expected = """# 1 "dummy.t"


        struct command commands[] =
        {
          { "quit", quit_command },
          { "help", help_command },
        };"""
        self.preprocess(src, expected)

    def test_ternary_operator_grouping(self):
        src = r"""#if (1 ? 2 ? 3 ? 3 : 2 : 1 : 0) != 3
        #error bad grouping
        #endif"""
        expected = """# 1 "dummy.t"


"""
        self.preprocess(src, expected)

    def test_ternary_operator_grouping2(self):
        src = r"""#if (0 ? 2 : 0 ? 3 : 2 ? 1 : 0) != 1
        #error bad grouping
        #endif"""
        expected = """# 1 "dummy.t"


"""
        self.preprocess(src, expected)

    def test_builtin_macros(self):
        src = r"""
        __FILE__;__LINE__
        __LINE__;__FILE__"""
        expected = '''# 1 "dummy.t"

        "dummy.t";2
        3;"dummy.t"'''
        self.preprocess(src, expected)

    @unittest.skip('TODO, fix time mock?')
    def test_builtin_time_macros(self):
        src = r"""
        __DATE__;__TIME__;"""
        expected = '''# 1 "dummy.t"

        "19 apr 2017";"12:34:56"'''
        self.preprocess(src, expected)

    def test_token_glue(self):
        """ Check various concatenations """
        src = r"""#define A(x,y) x ## y
        A(b,2)
        A(2,L)
        A(3,31)"""
        expected = """# 1 "dummy.t"

        b2
        2L
        331"""
        self.preprocess(src, expected)

    def test_token_invalid_concatenation(self):
        """ Check invalid concatenation """
        src = r"""#define A(x,y) x ## y
        A(:,;)"""
        with self.assertRaises(CompilerError) as cm:
            self.preprocess(src)
        self.assertEqual(2, cm.exception.loc.row)
        self.assertEqual(11, cm.exception.loc.col)

    def test_argument_expansion(self):
        """ Check the behavior of macro arguments when used in stringify """
        src = r"""#define A(x) # x x
        #define B 55 - 3
        A(B)"""
        expected = """# 1 "dummy.t"


        "B" 55 - 3"""
        self.preprocess(src, expected)

    def test_argument_prescan(self):
        """ When argument is used in concatenation, do not expand it """
        src = r"""#define AFTERX(x) X_ ## x
        #define XAFTERX(x) AFTERX(x)
        #define TABLESIZE w1024
        #define BUFSIZE TABLESIZE
        AFTERX(BUFSIZE)
        XAFTERX(BUFSIZE)"""
        expected = """# 1 "dummy.t"




        X_BUFSIZE
        X_w1024"""
        self.preprocess(src, expected)

    @unittest.skip('TODO!')
    def test_argument_prescan2(self):
        """ Example from gnu argument prescan website:

        https://gcc.gnu.org/onlinedocs/cpp/Argument-Prescan.html """
        src = r"""#define foo a,b
        #define bar(x) lose(x)
        #define lose(x) (1 + (x))
        bar(foo)"""
        expected = """# 1 "dummy.t"



        (1 + (a,b))"""
        self.preprocess(src, expected)


def gen_tokens(tokens):
    """ Helper function which creates a token iterator """
    col = 1
    for typ, val in tokens:
        loc = lexer.SourceLocation('test.c', 1, col, 1)
        yield lexer.CToken(typ, val, '', False, loc)
        col += 1


class CParserTestCase(unittest.TestCase):
    """ Test the C parser """
    def setUp(self):
        self.parser = CParser(COptions())

    def parse(self, tokens):
        cu = self.parser.parse(gen_tokens(tokens))
        return cu

    def test_empty(self):
        """ Test the obvious empty case! """
        cu = self.parse([])
        self.assertEqual(0, len(cu.declarations))

    def test_global_int(self):
        """ Test the parsing of a global integer """
        tokens = [('int', 'int'), ('ID', 'A'), (';', ';')]
        cu = self.parse(tokens)
        self.assertEqual(1, len(cu.declarations))
        decl = cu.declarations[0]
        self.assertEqual('A', decl.name)

    def test_function(self):
        """ Test the parsing of a function """
        tokens = [
            ('int', 'int'), ('ID', 'add'), ('(', '('), ('int', 'int'),
            ('ID', 'x'), (',', ','), ('int', 'int'), ('ID', 'y'), (')', ')'),
            ('{', '{'), ('return', 'return'), ('ID', 'x'), ('+', '+'),
            ('ID', 'y'), (';', ';'), ('}', '}')]
        cu = self.parse(tokens)
        self.assertEqual(1, len(cu.declarations))
        decl = cu.declarations[0]
        self.assertIsInstance(decl.typ, nodes.FunctionType)
        self.assertIsInstance(decl.typ.return_type, nodes.IdentifierType)
        stmt = decl.body.statements[0]
        self.assertIsInstance(stmt, nodes.Return)
        self.assertIsInstance(stmt.value, nodes.Binop)
        self.assertEqual('+', stmt.value.op)


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """
    def setUp(self):
        self.builder = CBuilder(ExampleArch(), COptions())

    def do(self, src):
        f = io.StringIO(src)
        ir_module = self.builder.build(f, None)
        assert isinstance(ir_module, ir.Module)
        Verifier().verify(ir_module)

    def test_1(self):
        src = """
        int a;
        void main(int b) {
         a = 10 + b;
        }
        """
        self.do(src)

    def test_2(self):
        src = """
        static int c, d, e;
        static float x;
        char f, g;
        int main() {
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
          return d;
        }
        """
        self.do(src)

    def test_control_structures(self):
        src = """
        int main() {
          int d,i,c;
          c = 2;
          d = 20 + c * 10 + c >> 2 - 123;
          if (d < 10)
          {
            while (d < 20)
            {
              d = d + c * 4;
            }
          }

          if (d > 20)
          {
            do {
              d += c;
            } while (d < 100);
          }
          else
          {
            for (i=i;i<10;i++)
            {

            }
          }
          return d;
        }
        """
        self.do(src)

    def test_4(self):
        """ Test expressions """
        src = """
        int main(int, int c) {
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
          return d;
        }
        """
        self.do(src)

    def test_5(self):
        src = """
        static int G;
        void initialize(int g)
        {
          G = g;
        }
        int main(int, int c) {
          int d = 2;
          initialize(d);
          return d;
        }
        """
        self.do(src)


class CastXmlTestCase(unittest.TestCase):
    """ Try out cast xml parsing. """
    def test_test8(self):
        reader = CastXmlReader()
        cu = reader.process(relpath('data', 'c', 'test8.xml'))


if __name__ == '__main__':
    unittest.main()
