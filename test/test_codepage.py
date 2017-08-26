
import unittest
import io
import ctypes
from util import make_filename
from ppci.api import cc, get_current_platform
from ppci.utils.codepage import load_code_as_module, platform_supported
from ppci.utils.codepage import load_obj
from ppci.utils.reporting import HtmlReportGenerator


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

    def test_c(self):
        """ Test loading of C code """
        source = io.StringIO("int x(int a) { return a + 1 ; }")
        arch = get_current_platform()
        obj = cc(source, arch, debug=True)
        m = load_obj(obj)
        y = m.x(101)
        self.assertEqual(102, y)

    @unittest.skip('TODO: research array index handling')
    def test_jit_example(self):
        """ Test loading of C code from jit example """
        source = io.StringIO("""
        long x(long* a, long* b, long count) {
          long sum = 0;
          long i;
          for (i=0; i < count; i++)
            sum += a[i] * b[i];
          return sum;
        }
        """)
        arch = get_current_platform()
        html_filename = make_filename(self.id()) + '.html'
        with open(html_filename, 'w') as f:
            with HtmlReportGenerator(f) as reporter:
                obj = cc(source, arch, debug=True, reporter=reporter)
        m = load_obj(obj)
        print(m.x.argtypes)
        T = ctypes.c_long * 3
        a = T()
        a[:] = 1, 2, 3
        ap = ctypes.cast(a, ctypes.POINTER(ctypes.c_long))
        b = T()
        b[:] = 5, 4, 9
        bp = ctypes.cast(b, ctypes.POINTER(ctypes.c_long))
        y = m.x(a, b, 3)
        self.assertEqual(40, y)


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
        html_filename = make_filename(self.id()) + '.html'
        with open(html_filename, 'w') as f:
            with HtmlReportGenerator(f) as reporter:
                m = load_code_as_module(source_file, reporter=reporter)

        import numpy as np
        a = np.array([12, 7, 3, 5, 42, 8, 3, 5, 8, 1, 4, 6, 2], dtype=int)
        addr = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_int))

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

        ap = ctypes.cast(a.ctypes.data, ctypes.POINTER(ctypes.c_double))
        bp = ctypes.cast(b.ctypes.data, ctypes.POINTER(ctypes.c_double))

        m.mlt(ap, bp, len(a), a.itemsize)
        # print(a)
        # print(c)
        self.assertTrue(np.allclose(c, a))


if __name__ == '__main__':
    unittest.main()
