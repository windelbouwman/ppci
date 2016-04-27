import unittest
import io
from ppci.lang.c import CBuilder, Printer
from ppci.arch.example import ExampleArch


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
