import unittest
import io
from ppci.api import cc, get_arch


class InlineAsmTestCase(unittest.TestCase):
    def test_inline_asm(self):
        """Test the compilation of inline assembly code."""
        src = """
        int foo(int a, int b, char c) {
            asm (
                "mov rsi, %0\n"
                "xor rsi, %1\n"
                "and rsi, %1\n"
                :
                : "r" (a), "r" (c)
                : "rsi"
            );
            return b;
        }
        """
        march = get_arch("x86_64")
        cc(io.StringIO(src), march)


if __name__ == "__main__":
    unittest.main()
