import unittest
import io
from ppci.api import cc, get_arch


class InlineAsmTestCase(unittest.TestCase):
    def test_inline_asm(self):
        """ Test the compilation of inline assembly code. """
        src = """
        int foo(int a, int b, char c) {
            asm (
                "xor %0, %1"
                :
                : "r" (a), "r" (c)
            );
        }
        """
        march = get_arch('x86_64')
        cc(io.StringIO(src), march)


if __name__ == '__main__':
    unittest.main()
