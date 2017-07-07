import unittest
import io
from unittest import mock
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, CPreProcessor, CLexer, lexer, CParser, nodes
from ppci.lang.c import CContext, COptions
from ppci.lang.c.preprocessor import CTokenPrinter, prepare_for_parsing


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

    @mock.patch('time.strftime', lambda fmt: 'mastah')
    def test_builtin_time_macros(self):
        src = r"""
        __DATE__;__TIME__;"""
        expected = '''# 1 "dummy.t"

        "mastah";"mastah";'''
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

    @unittest.skip('TODO!')
    def test_variable_arguments(self):
        """ Check the behavior of variable arguments """
        src = r"""#define A(...) a __VA_ARGS__ b
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


if __name__ == '__main__':
    unittest.main()
