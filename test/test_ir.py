import unittest
import sys
import io
from ppci import ir
from ppci import irutils
from ppci.transform import ConstantFolder
from ppci.buildfunctions import ir_to_python, bf2ir
from util import relpath


class IrCodeTestCase(unittest.TestCase):
    def testAdd(self):
        """ See if the ir classes can be constructed """
        v1 = ir.Const(1, 'const', ir.i32)
        v2 = ir.Const(2, 'const', ir.i32)
        ir.Add(v1, v2, "add", ir.i32)

    def testUse(self):
        """ Check if use def information is correctly administered """
        c1 = ir.Const(1, 'one', ir.i32)
        c2 = ir.Const(2, 'two', ir.i32)
        c3 = ir.Const(3, 'three', ir.i32)
        c4 = ir.Const(4, 'four', ir.i32)
        add = ir.Add(c1, c2, 'add', ir.i32)
        self.assertEqual({c1, c2}, add.uses)

        # Replace usage by setting the variable:
        add.a = c3
        self.assertEqual({c3, c2}, add.uses)

        # Replace use by changing value:
        add.replace_use(c2, c4)
        self.assertEqual({c3, c4}, add.uses)
        self.assertEqual(c4, add.b)


class IrBuilderTestCase(unittest.TestCase):
    def setUp(self):
        self.b = irutils.Builder()
        self.m = ir.Module('test')
        self.b.setModule(self.m)

    def testBuilder(self):
        f = self.b.new_function('add')
        self.b.setFunction(f)
        bb = self.b.newBlock()
        self.b.emit(ir.Jump(bb))
        self.b.setBlock(bb)
        self.b.emit(ir.Const(0, 'const', ir.i32))
        self.b.emit(ir.Jump(f.epilog))
        # Run interpreter:
        # r = self.m.getFunction('add').call(1, 2)
        #self.assertEqual(3, r)


class ConstantFolderTestCase(unittest.TestCase):
    def setUp(self):
        self.b = irutils.Builder()
        self.cf = ConstantFolder()
        self.m = ir.Module('test')
        self.b.setModule(self.m)

    def testBuilder(self):
        f = self.b.new_function('test')
        self.b.setFunction(f)
        bb = self.b.newBlock()
        self.b.emit(ir.Jump(bb))
        self.b.setBlock(bb)
        v1 = self.b.emit(ir.Const(5, 'const', ir.i32))
        v2 = self.b.emit(ir.Const(7, 'const', ir.i32))
        self.b.emit(ir.Add(v1, v2, "add", ir.i32))
        self.b.emit(ir.Jump(f.epilog))
        self.cf.run(self.m)

    def testAdd0(self):
        f = self.b.new_function('test')
        self.b.setFunction(f)
        self.b.setBlock(self.b.newBlock())
        v1 = ir.Const(12, 'const', ir.i32)
        self.b.emit(v1)
        v2 = ir.Const(0, 'const', ir.i32)
        self.b.emit(v2)
        v3 = ir.Add(v1, v2, "add", ir.i32)
        self.b.emit(v3)


class TestWriter(unittest.TestCase):
    def testWrite(self):
        writer = irutils.Writer()
        module = ir.Module('mod1')
        function = ir.Function('func1', module)
        f = io.StringIO()
        writer.write(module, f)
        f2 = io.StringIO(f.getvalue())
        reader = irutils.Reader()
        # TODO: fix read back
        #module2 = reader.read(f2)
        #f3 = io.StringIO()
        #writer.write(module2, f3)
        #self.assertEqual(f3.getvalue(), f.getvalue())


class TestReader(unittest.TestCase):
    def testAddExample(self):
        reader = irutils.Reader()
        with open(relpath('data', 'add.pi')) as f:
            m = reader.read(f)
            self.assertTrue(m)
            #print(m)


class TestIrToPython(unittest.TestCase):
    def testAddExample(self):
        reader = irutils.Reader()
        with open(relpath('data', 'add.pi')) as f:
            m = reader.read(f)
            writer = irutils.Writer()
            # writer.write(m, sys.stdout)
            # ir_to_python(m)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
