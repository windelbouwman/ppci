
import unittest
import io
import ctypes
from ppci.utils.codepage import load_code_as_module


def has_numpy():
    try:
        import numpy as np
        return True
    except ImportError:
        return False


class TestCase(unittest.TestCase):
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

    @unittest.skipIf(not has_numpy(), 'skipping numpy test')
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

        # TODO: the argument types should be inferred:
        m.find_first.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

        # Cross fingers
        pos = m.find_first(addr, 42, len(a), a.itemsize)
        self.assertEqual(4, pos)

        pos = m.find_first(addr, 200, len(a), a.itemsize)
        self.assertEqual(0xff, pos)


if __name__ == '__main__':
    unittest.main()
