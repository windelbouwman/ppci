
import io
import unittest
from ppci.api import cc, link


class StaticLinkTestCase(unittest.TestCase):
    def test_static_link(self):
        arch = 'arm'
        o1 = cc(io.StringIO("""
        static int add(int a, int b) {
            return a + b;
        }
        int voodoo1(int a) {
            return add(a, 12);
        }
        """), arch)
        o2 = cc(io.StringIO("""
        static int add(int a, int b) {
            return a + b;
        }
        int voodoo2(int a) {
            return add(a, 12);
        }
        """), arch)
        link([o1, o2])


if __name__ == '__main__':
    unittest.main()
