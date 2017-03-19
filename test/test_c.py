import unittest
import io
from ppci.lang.c import CBuilder, Printer, CPreProcessor
from ppci.arch.example import ExampleArch


class CPreProcessorTestCase(unittest.TestCase):
    def setUp(self):
        self.preprocessor = CPreProcessor()

    def preprocess(self, src):
        f = io.StringIO(src)
        tokens = self.preprocessor.process(f, None)

        print(list(tokens))

    def test_simple_define(self):
        src = r"""
        #define A 100
        printf("%i\n", A);
        """
        self.preprocess(src)

    def test_ifdef(self):
        src = r"""
        #ifdef A
        printf("%i\n", A);
        #else
        printf("%i\n", 100);
        #endif
        """
        self.preprocess(src)


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
