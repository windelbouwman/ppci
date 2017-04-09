import unittest
import io
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, Printer, CPreProcessor, CLexer, lexer
from ppci.lang.c.preprocessor import CTokenPrinter
from ppci.lang.c.options import COptions
from ppci.arch.example import ExampleArch


class CLexerTestCase(unittest.TestCase):
    """ Test the behavior of the lexer """
    def setUp(self):
        coptions = COptions()
        self.lexer = CLexer(coptions)
        coptions.enable('trigraphs')

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
        tokens = list(self.lexer.lex(io.StringIO(src), 'a.h'))
        self.assertSequenceEqual(['Hello', 'world'], [t.val for t in tokens])
        self.assertSequenceEqual([1, 2], [t.loc.row for t in tokens])
        self.assertSequenceEqual([1, 3], [t.loc.col for t in tokens])
        self.assertSequenceEqual(['', ' '], [t.space for t in tokens])
        self.assertSequenceEqual([True, False], [t.first for t in tokens])

    def test_block_comment(self):
        src = "/* bla bla */"
        tokens = list(self.lexer.lex(io.StringIO(src), 'a.h'))


class CPreProcessorTestCase(unittest.TestCase):
    """ Test the preprocessor functioning """
    def setUp(self):
        self.preprocessor = CPreProcessor(COptions())

    def preprocess(self, src, expected=None):
        f = io.StringIO(src)
        lines = self.preprocessor.process(f, None)

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
        expected = r"""

        printf("%i\n",100);"""
        self.preprocess(src, expected)

    def test_recursive_define(self):
        src = r"""
        #define A(X,Y) (100 + X + (Y))
        A(A(1,2),A(A(23,G),22))"""
        expected = r"""

        (100 + (100 + 1 + (2)) + ((100 + (100 + 23 + (G)) + (22))))"""
        self.preprocess(src, expected)

    def test_ifdef(self):
        src = r"""
        #ifdef A
        printf("%i\n", A);
        #else
        printf("%i\n", 100);
        #endif
        """
        expected = r"""


        printf("%i\n", 100);

"""
        self.preprocess(src, expected)

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
        expected = r"""
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
        expected = r"""





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
        expected = r"""

        123"""
        self.preprocess(src, expected)

    def test_cpplib_example(self):
        """ Test a nested function like macro """
        src = r"""#define foo(x) bar x
        foo(foo
        ) (2)"""
        expected = r"""
        bar foo (2)"""
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
        src = r"""#define COMMAND(NAME)  { #NAME, NAME ## _command }
        struct command commands[] =
        {
          COMMAND(quit),
          COMMAND(help),
        };"""
        expected = """
        struct command commands[] =
        {
          { "quit", quit_command },
          { "help", help_command },
        };"""
        self.preprocess(src, expected)

    @unittest.skip('TODO!')
    def test_argument_prescan(self):
        src = r"""#define AFTERX(x) X_ ## x
        #define XAFTERX(x) AFTERX(x)
        #define TABLESIZE w1024
        #define BUFSIZE TABLESIZE
        AFTERX(BUFSIZE)
        XAFTERX(BUFSIZE)"""
        expected = """



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
        expected = """


        X_w1024"""
        self.preprocess(src, expected)


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """
    def setUp(self):
        self.builder = CBuilder(ExampleArch(), COptions())

    def do(self, src):
        f = io.StringIO(src)
        self.builder.build(f)

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
        static float c, d, e;
        char f, g;
        int main() {
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
        }
        """
        self.do(src)


if __name__ == '__main__':
    unittest.main()
