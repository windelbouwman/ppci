import unittest
import sys
from ppci import ir
from ppci import irutils
from ppci.irutils import Verifier
from ppci.opt.mem2reg import Mem2RegPromotor


class CleanTestCase(unittest.TestCase):
    def setUp(self):
        self.b = irutils.Builder()
        self.m = ir.Module('test')
        self.b.set_module(self.m)
        self.verifier = Verifier()

    def test_glue_blocks(self):
        f = self.b.new_function('add')
        self.b.set_function(f)


class Mem2RegTestCase(unittest.TestCase):
    """ Test the memory to register lifter """
    def setUp(self):
        self.builder = irutils.Builder()
        self.module = ir.Module('test')
        self.builder.set_module(self.module)
        self.function = self.builder.new_function('add')
        self.builder.set_function(self.function)
        self.verifier = Verifier()
        self.mem2reg = Mem2RegPromotor()

    def tearDown(self):
        self.verifier.verify(self.module)

    def test_normal_use(self):
        alloc = self.builder.emit(ir.Alloc('A', 4))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i32))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i32))
        self.builder.emit(ir.Jump(self.function.epilog))
        self.mem2reg.run(self.module)
        self.assertNotIn(alloc, self.function.entry.instructions)

    def test_byte_lift(self):
        """ Test byte data type to work """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i8))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8))
        self.builder.emit(ir.Jump(self.function.epilog))
        self.mem2reg.run(self.module)
        self.assertNotIn(alloc, self.function.entry.instructions)

    def test_volatile_not_lifted(self):
        """ Volatile allocs must persist """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i8))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8, volatile=True))
        self.builder.emit(ir.Jump(self.function.epilog))
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)

    def test_different_type_not_lifted(self):
        """ different types must persist """
        alloc = self.builder.emit(ir.Alloc('A', 1))
        cnst = self.builder.emit(ir.Const(1, 'cnst', ir.i32))
        self.builder.emit(ir.Store(cnst, alloc))
        self.builder.emit(ir.Load(alloc, 'Ld', ir.i8))
        self.builder.emit(ir.Jump(self.function.epilog))
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)

    def test_store_uses_alloc_as_value(self):
        """ When only stores and loads use the alloc, the store can use the
        alloc as a value. In this case, the store must remain """
        alloc = self.builder.emit(ir.Alloc('A', 4))
        self.builder.emit(ir.Store(alloc, alloc))
        self.builder.emit(ir.Jump(self.function.epilog))
        self.mem2reg.run(self.module)
        self.assertIn(alloc, self.function.entry.instructions)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
