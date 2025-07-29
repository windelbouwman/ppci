import unittest
import io
from unittest import mock
from ppci.common import CompilerError
from ppci.lang.c import CPreProcessor
from ppci.lang.c import COptions
from ppci.lang.c import CTokenPrinter


class CPreProcessorTestCase(unittest.TestCase):
    """Test the preprocessor functioning"""

    def setUp(self):
        coptions = COptions()
        coptions.enable("verbose")
        self.preprocessor = CPreProcessor(coptions)

    def preprocess(self, src: str, expected=None):
        f = io.StringIO(src)
        tokens = self.preprocessor.process_file(f, "dummy.t")
        tokens = list(tokens)
        print(tokens)

        f2 = io.StringIO()
        CTokenPrinter().dump(tokens, file=f2)
        actual_output = f2.getvalue()
        if expected:
            self.assertEqual(expected, actual_output)

    def test_empty(self):
        """Test the obvious empty case!"""
        self.preprocess("", "")

    def test_simple_define(self):
        src = r"""
        #define A 100
        printf("%i\n",A);"""
        expected = r"""# 1 "dummy.t"


        printf("%i\n",100);"""
        self.preprocess(src, expected)

    def test_null_directive(self):
        """Test null directive."""
        src = r"""
        #
        x"""
        expected = r"""# 1 "dummy.t"


        x"""
        self.preprocess(src, expected)

    def test_recursive_define(self):
        """Test recursive function like macro."""
        src = r"""
        #define A(X,Y) (100 + X + (Y))
        A(A(1,2),A(A(23,G),22))"""
        expected = r"""# 1 "dummy.t"


        (100 + (100 + 1 + (2)) + ((100 + (100 + 23 + (G)) + (22))))"""
        self.preprocess(src, expected)

    def test_if_expression(self):
        """The #if preprocessor directive."""
        src = r"""#if L'\0'-1 > 0
        unsigned wide char
        #endif
        end"""
        expected = r"""# 1 "dummy.t"



        end"""
        self.preprocess(src, expected)

    def test_expression_binding(self):
        """Test if operator associativity is correct."""
        src = r"""
        #if 2 * 3 / 2 == 3
        ok
        #endif
        end"""
        expected = r"""# 1 "dummy.t"


        ok

        end"""
        self.preprocess(src, expected)

    def test_boolean_expression_value(self):
        """Test the value of logical operators."""
        src = r"""
        #if (7 && 3) == 1
        ok1
        #endif

        #if (7 || 3) == 1
        ok2
        #endif

        #if (0 || 3) == 1
        ok3
        #endif
        end"""
        expected = r"""# 1 "dummy.t"


        ok1



        ok2



        ok3

        end"""
        self.preprocess(src, expected)

    def test_empty_macro_expansion(self):
        """See what happens when on the next line, the first token is
        macro-expanded into nothing.

        Proper care should be taken to copy the beginning-of-line (BOL)
        marker.
        """
        src = r"""#define foo
        #if 1
        foo bla
        #endif
        """
        expected = r"""# 1 "dummy.t"

 bla

"""
        self.preprocess(src, expected)

    def test_ifdef(self):
        """Test #ifdef directive."""
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
        """Test #line directive and __LINE__ and __FILE__ macros."""
        src = r"""
        #define assert(e) _assert(e, __FILE__, __LINE__)
        assert(1);
        assert(2);
        #line 1234 "cpp"
        fubar
        __LINE__; __FILE__;
        #line 567
        fubar
        __LINE__; __FILE__;
        end"""
        expected = r"""# 1 "dummy.t"


        _assert(1, "dummy.t", 3);
        _assert(2, "dummy.t", 4);

        fubar
        1235; "cpp";

        fubar
        568; "cpp";
        end"""
        self.preprocess(src, expected)

    def test_error_directive(self):
        src = r"""
        #error this is not yet implemented 1234 #&!*^"""
        with self.assertRaises(CompilerError) as cm:
            self.preprocess(src)
        self.assertEqual(2, cm.exception.loc.row)
        self.assertEqual(
            "this is not yet implemented 1234 #&!*^", cm.exception.msg
        )

    def test_intermediate_example(self):
        """Check a medium hard example"""
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
        """Check a hard example"""
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
        """Test a scandalous use of the preprocessor"""
        src = r"""#define function() 123
        #define concat(a,b) a ## b
        concat(func,tion)()"""
        expected = r"""# 1 "dummy.t"


        123"""
        self.preprocess(src, expected)

    def test_cpplib_example(self):
        """Test a nested function like macro on multiple lines.

        https://gcc.gnu.org/onlinedocs/cppinternals.pdf
        """
        src = r"""#define foo(x) bar x
        foo(foo
        ) (2)"""
        expected = r"""# 1 "dummy.t"

        bar foo (2)"""
        self.preprocess(src, expected)

    def test_if_expression_single_line(self):
        """Test if which might roll over to the next line!

        This case requires to stay on the line with the if on it.
        """
        src = r"""
        #define X 1
        if (1 > 2
        #if !X
        &&
        #else
        ||
        #endif"""
        expected = r"""# 1 "dummy.t"


        if (1 > 2



        ||
"""
        self.preprocess(src, expected)

    def test_if(self):
        """Test elif with else"""
        src = r"""/* test with comments */
        #define __WORDSIZE 32  /* use 32 */
        #if __WORDSIZE == 32  /* woei */
        int32
        #elif __WORDSIZE == 64 // line comment
        int64
        #else
        int999
        #endif"""
        expected = r"""# 1 "dummy.t"



        int32




"""
        self.preprocess(src, expected)

    def test_elif(self):
        """Test elif with else"""
        src = r"""/* test with comments */
        #define __WORDSIZE 64  /* use 64 */
        #if __WORDSIZE == 32  /* woei */
        int32
        #elif __WORDSIZE == 64 // line comment
        int64
        #else
        int999
        #endif"""
        expected = r"""# 1 "dummy.t"





        int64


"""
        self.preprocess(src, expected)

    def test_mismatching_endif(self):
        """Test stray #endif directive."""
        src = r"""     #endif   """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_mismatching_else(self):
        """Test wild #else directive."""
        src = r"""     #else   """
        with self.assertRaises(CompilerError):
            self.preprocess(src)

    def test_double_else(self):
        """Test misplaced #else directive."""
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
        """Test a typical use case of token glueing."""
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
        __LINE__;__FILE__
        __COUNTER__
        __COUNTER__
        __COUNTER__"""
        expected = """# 1 "dummy.t"

        "dummy.t";2
        3;"dummy.t"
        0
        1
        2"""
        self.preprocess(src, expected)

    @mock.patch("time.strftime", lambda fmt: '"mastah"')
    def test_builtin_time_macros(self):
        """Test builtin macros __DATE__ and __TIME__"""
        src = r"""
        __DATE__;__TIME__;"""
        expected = """# 1 "dummy.t"

        "mastah";"mastah";"""
        self.preprocess(src, expected)

    def test_empty_arguments(self):
        """Check empty arguments"""
        src = r"""#define A(); // comments!
        #define B();
        A();
        B();"""
        expected = """# 1 "dummy.t"


        ;;
        ;;"""
        self.preprocess(src, expected)

    def test_stringify(self):
        """Test token stringification."""
        src = r"""#define S(a) #a
        S(word)
        S("string")
        S('a')
        S('"')
        S("aa\tbb")
        S( 1)
        S(  1    2    3  )
        E"""
        expected = r"""# 1 "dummy.t"

        "word"
        "\"string\""
        "'a'"
        "'\"'"
        "\"aa\\tbb\""
        "1"
        "1 2 3"
        E"""
        self.preprocess(src, expected)

    def test_token_glue(self):
        """Check various concatenations"""
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
        """Check invalid concatenation"""
        src = r"""#define A(x,y) x ## y
        A(:,;)"""
        with self.assertRaises(CompilerError) as cm:
            self.preprocess(src)
        self.assertEqual(2, cm.exception.loc.row)
        self.assertEqual(11, cm.exception.loc.col)

    def test_argument_expansion(self):
        """Check the behavior of macro arguments when used in stringify"""
        src = r"""#define A(x) # x x
        #define B 55 - 3
        A(B)"""
        expected = """# 1 "dummy.t"


        "B" 55 - 3"""
        self.preprocess(src, expected)

    def test_variadic_macro(self):
        """Check the behavior of variadic macros"""
        src = r"""#define A(...) a __VA_ARGS__ b
        A(B)
        A(2, 4,5)
        A(  2  ,   4   ,  5  )
        A(  2    9  ,   4   8 ,  5   8   )
        A(2    9,4   8,5   8)
        A(2,4,5)
        E"""
        expected = """# 1 "dummy.t"

        a B b
        a 2, 4,5 b
        a 2 , 4 , 5 b
        a 2 9 , 4 8 , 5 8 b
        a 2 9,4 8,5 8 b
        a 2,4,5 b
        E"""
        self.preprocess(src, expected)

    def test_named_variadic_macro(self):
        """Check the behavior of variadic macros"""
        src = r"""#define A(NAME...) a NAME b
        A(B)
        E"""
        expected = """# 1 "dummy.t"

        a B b
        E"""
        self.preprocess(src, expected)

    def test_argument_prescan(self):
        """When argument is used in concatenation, do not expand it"""
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

    def test_macro_arguments(self):
        """Test the amount of comma's in macro arguments.

        Test both variadic and fixed count argument macros.
        """
        src = r"""
        #define M(arg) w00t arg w44t
        M(;)
        M()

        #define CALL(f, ...) (f)(__VA_ARGS__)
        CALL(g0)
        CALL(g0, 1)
        CALL(g0, 1, 2)
        CALL(g0, 1, 2, 3)
        E"""
        expected = r"""# 1 "dummy.t"


        w00t ; w44t
        w00t w44t


        (g0)()
        (g0)(1)
        (g0)(1, 2)
        (g0)(1, 2, 3)
        E"""
        self.preprocess(src, expected)

    @unittest.skip("TODO!")
    def test_argument_prescan2(self):
        """Example from gnu argument prescan website.

        https://gcc.gnu.org/onlinedocs/cpp/Argument-Prescan.html"""
        src = r"""#define foo a,b
        #define bar(x) lose(x)
        #define lose(x) (1 + (x))
        bar(foo)"""
        expected = """# 1 "dummy.t"



        (1 + (a,b))"""
        self.preprocess(src, expected)

    def test_single_line_comment(self):
        """Line comment issue"""
        src = r"""// error
        void main() {// ok }
        """
        expected = r"""# 1 "dummy.t"

        void main() {
"""
        self.preprocess(src, expected)


if __name__ == "__main__":
    unittest.main()
