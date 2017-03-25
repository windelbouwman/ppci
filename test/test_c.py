import unittest
import io
from ppci.lang.c import CBuilder, Printer, CPreProcessor
from ppci.lang.c.preprocessor import CTokenPrinter
from ppci.arch.example import ExampleArch


class CPreProcessorTestCase(unittest.TestCase):
    def setUp(self):
        self.preprocessor = CPreProcessor()

    def preprocess(self, src, expected=None):
        f = io.StringIO(src)
        lines = self.preprocessor.process(f, None)

        f2 = io.StringIO()
        CTokenPrinter().dump(lines, file=f2)
        actual_output = f2.getvalue()
        if expected:
            self.assertEqual(expected, actual_output)

    def test_simple_define(self):
        src = r"""
        #define A 100
        printf("%i\n", A);
        """
        expected = r"""

        printf("%i\n", 100);

"""
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
        }
        """
        expected = r"""
        int X = A;

        int B = 5;




        int X=0;



 defined( 100 + 55 + B) && defined 55 + B 100 + 55 + B



        int g = 56;


        int defined = 2;
        int main()
        {
        printf("%i\n", 100 + 55 + B);
        }

"""
        self.preprocess(src, expected)

    def test_hard_example(self):
        """ Check a hard example """
        src = r"""
        #define A(B,C) 100 + B + # C
        #define B 55 + B
        #define D(x,y) x ## _ ## y

        A(2,3)
        D(wa,ttuh)
        """
        expected = r"""




 100 +2 +"3"
wa_ttuh

"""
        self.preprocess(src, expected)


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """
    def setUp(self):
        self.builder = CBuilder(ExampleArch())

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
