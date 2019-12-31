import unittest
import io

from ppci import ir
from ppci.irutils import Verifier
from ppci.lang.c import CBuilder
from ppci.lang.c.options import COptions
from ppci.arch.example import ExampleArch
from ppci.lang.c import CSynthesizer


class CSynthesizerTestCase(unittest.TestCase):
    def test_hello(self):
        """ Convert C to Ir, and then this IR to C """
        src = r"""
        void printf(char*);
        void main(int b) {
          printf("Hello" "world\n");
        }
        """
        arch = ExampleArch()
        builder = CBuilder(arch.info, COptions())
        f = io.StringIO(src)
        ir_module = builder.build(f, None)
        assert isinstance(ir_module, ir.Module)
        Verifier().verify(ir_module)
        synthesizer = CSynthesizer()
        synthesizer.syn_module(ir_module)


if __name__ == '__main__':
    unittest.main()
