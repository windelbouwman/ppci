"""
    Optimalization tests.
"""
import unittest
import io
import sys
from ppci import ir
from ppci import irutils
from ppci.binutils.debuginfo import DebugDb
from ppci.irutils import Verifier
from ppci.opt import Mem2RegPromotor
from ppci.opt import CleanPass
from ppci.opt.constantfolding import correct


class OptTestCase(unittest.TestCase):
    """ Base testcase that prepares a module, builder and verifier """
    def setUp(self):
        self.builder = irutils.Builder()
        self.module = ir.Module('test')
        self.builder.set_module(self.module)
        self.function = self.builder.new_procedure('testfunction')
        self.builder.set_function(self.function)
        entry = self.builder.new_block()
        self.function.entry = entry
        self.builder.set_block(entry)
        self.verifier = Verifier()
        self.debug_db = DebugDb()

    def dump(self):
        writer = irutils.Writer()
        iof = io.StringIO()
        writer.write(self.module, iof)
        print(iof.getvalue())

    def tearDown(self):
        self.verifier.verify(self.module)


class CleanTestCase(OptTestCase):
    """ Test the clean pass for correct function """
    def setUp(self):
        super().setUp()
        self.clean_pass = CleanPass(self.debug_db)

    def test_glue_blocks(self):
        epilog = self.builder.new_block()
        self.builder.emit(ir.Jump(epilog))
        self.builder.set_block(epilog)
        self.builder.emit(ir.Exit())

    def test_glue_with_phi(self):
        """
            After replacing the predecessor, the use info of a phi is messed
            up.
        """
        block1 = self.builder.new_block()
        block4 = self.builder.new_block()  # This one must be eliminated
        block6 = self.builder.new_block()
        self.builder.emit(ir.Jump(block1))
        self.builder.set_block(block1)
        cnst = self.builder.emit(ir.Const(0, 'const', ir.i16))
        self.builder.emit(ir.Jump(block4))
        self.builder.set_block(block4)
        self.builder.emit(ir.Jump(block6))
        self.builder.set_block(block6)
        phi = self.builder.emit(ir.Phi('res24', ir.i16))
        phi.set_incoming(block4, cnst)
        cnst2 = self.builder.emit(ir.Const(2, 'cnst2', ir.i16))
        binop = self.builder.emit(ir.add(phi, cnst2, 'binop', ir.i16))
        phi.set_incoming(block6, binop)
        self.builder.emit(ir.Jump(block6))
        self.verifier.verify(self.module)

        # Act:
        self.clean_pass.run(self.module)
        self.assertNotIn(block4, self.function)


class Mem2RegTestCase(OptTestCase):
    """ Test the memory to register lifter """
    def setUp(self):
        super().setUp()
        self.mem2reg = Mem2RegPromotor(self.debug_db)

    def test_normal_use(self):
        alloc = self.builder.emit(ir.Alloc('A', 4))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i32))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i32))
        self.builder.emit(ir.Exit())
        self.mem2reg.run(self.module)
        self.assertNotIn(alloc, self.function.entry.instructions)

    def test_byte_lift(self):
        """ Test byte data type to work """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i8))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8))
        self.builder.emit(ir.Exit())
        self.mem2reg.run(self.module)
        self.assertNotIn(alloc, self.function.entry.instructions)

    def test_volatile_not_lifted(self):
        """ Volatile allocs must persist """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i8))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8, volatile=True))
        self.builder.emit(ir.Exit())
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)

    def test_different_type_not_lifted(self):
        """ different types must persist """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i32))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8))
        self.builder.emit(ir.Exit())
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)

    def test_store_uses_alloc_as_value(self):
        """ When only stores and loads use the alloc, the store can use the
        alloc as a value. In this case, the store must remain """
        alloc = self.builder.emit(ir.Alloc('A', 4))
        self.builder.emit(ir.Store(alloc, alloc))
        self.builder.emit(ir.Exit())
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)


class TypedEvalTestCase(unittest.TestCase):
    """ Test various integer values wrapped at bitsizes and signedness """
    def test_char_overflow(self):
        self.assertEqual(9, correct(9, ir.i8))
        self.assertEqual(-128, correct(127+1, ir.i8))
        self.assertEqual(127, correct(-128-1, ir.i8))
        self.assertEqual(-125, correct(4+127, ir.i8))

    def test_byte_overflow(self):
        self.assertEqual(8, correct(9+255, ir.u8))
        self.assertEqual(254, correct(-2, ir.u8))

    def test_u16_overflow(self):
        self.assertEqual(1, correct(2+65535, ir.u16))
        self.assertEqual(65534, correct(-2, ir.u16))
        self.assertEqual(1, correct(2+65535+65536*3, ir.u16))

    def test_i16_overflow(self):
        self.assertEqual(-32767, correct(2+32767, ir.i16))
        self.assertEqual(32766, correct(-32767-3, ir.i16))


if __name__ == '__main__':
    unittest.main()
    sys.exit()
