
import unittest
import io
import ctypes
from ppci.utils.codepage import load_code_as_module, platform_supported


def has_numpy():
    try:
        import numpy as np
        return True
    except ImportError:
        return False


@unittest.skipUnless(platform_supported(), 'skipping codepage tests')
class CodePageTestCase(unittest.TestCase):
    def test_add(self):
        source_file = io.StringIO("""
              module main;
              function int add(int a, int b) {
                return a + b;
              }

              function int sub(int a, int b) {
                return a - b;
              }
            """)
        m = load_code_as_module(source_file)

        # Cross fingers
        self.assertEqual(3, m.add(1, 2))
        self.assertEqual(8, m.sub(10, 2))

    def test_floated(self):
        """ Test floating point function """
        source_file = io.StringIO("""
            module main;
            function double add(double a, int b) {
                return a + b;
            }
            """)
        m = load_code_as_module(source_file)
        x = m.add(3.14, 101)
        # print(x, type(x))
        self.assertEqual(104.14, x)


@unittest.skipUnless(has_numpy() and platform_supported(), 'skipping codepage')
class NumpyCodePageTestCase(unittest.TestCase):
    def test_numpy(self):
        source_file = io.StringIO("""
            module main;
            function int find_first(int *a, int b, int size, int stride) {
                var int i = 0;
                var int ptr = 0;
                for ( i=0; i<size; i+=1 ) {
                  if ( *(a + ptr) == b ) {
                    return i;
                  }
                  ptr += stride;
                }

                return 0xff;
            }
            """)
        m = load_code_as_module(source_file)

        import numpy as np
        a = np.array([12, 7, 3, 5, 42, 8, 3, 5, 8, 1, 4, 6, 2], dtype=int)
        addr = a.ctypes.data

        # Cross fingers
        pos = m.find_first(addr, 42, len(a), a.itemsize)
        self.assertEqual(4, pos)

        pos = m.find_first(addr, 200, len(a), a.itemsize)
        self.assertEqual(0xff, pos)

    def test_numpy_floated(self):
        # TODO: add '10.2' instead of '10'. Somehow, adding 10.2 does not work
        source_file = io.StringIO("""
            module main;
            function void mlt(double* a, double *b, int size, int stride) {
                var int i = 0;
                var int ptr = 0;
                for ( i=0; i<size; i+=1 ) {
                  *(a + ptr) = *(a + ptr) + *(b + ptr) * 2 + 10;
                  ptr += stride;
                }
            }
            """)
        m = load_code_as_module(source_file)

        import numpy as np
        a = np.array([12, 7, 3, 5, 42, 100], dtype=float)
        b = np.array([82, 2, 5, 8, 13, 600], dtype=float)
        c = np.array([186, 21, 23, 31, 78, 1310], dtype=float)

        m.mlt(a.ctypes.data, b.ctypes.data, len(a), a.itemsize)
        # print(a)
        # print(c)
        self.assertTrue(np.allclose(c, a))


if __name__ == '__main__':
    unittest.main()
