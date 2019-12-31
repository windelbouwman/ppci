""" Test algorithms which reconstruct structured flow blocks from cfg """

import unittest
import io
from ppci.graph import relooper
from ppci import irutils


class RelooperTestCase(unittest.TestCase):
    def test_return_from_loop(self):
        """ Check the behavior when we return from within a loop """
        mod = """module foo;
        global procedure x() {
            block1: {
                jmp block2;
            }
            block2: {
                i32 a = 2;
                i32 b = 5;
                cjmp a < b ? block3 : block4;
            }
            block3: {
                exit;
            }
            block4: {
                i32 c = 2;
                i32 d = 5;
                cjmp c < d ? block5 : block6;
            }
            block5: {
                jmp block2;
            }
            block6: {
                exit;
            }
        }
        """
        ir_module = irutils.read_module(io.StringIO(mod))
        ir_function = ir_module['x']
        # print(ir_function)
        # irutils.print_module(ir_module)
        shape, _ = relooper.find_structure(ir_function)
        # relooper.print_shape(shape)
        # print(shape)


if __name__ == '__main__':
    unittest.main()
