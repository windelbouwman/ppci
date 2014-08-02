import unittest
import sys
import io
from ppci import ir
from ppci import irutils
from ppci.transform import ConstantFolder


class IrCodeTestCase(unittest.TestCase):
    def testAdd(self):
        """ See if the ir classes can be constructed """
        v1 = ir.Const(1, 'const', ir.i32)
        v2 = ir.Const(2, 'const', ir.i32)
        ir.Add(v1, v2, "add", ir.i32)


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
        self.b.emit(ir.Jump(f.epiloog))
        # Run interpreter:
        # r = self.m.getFunction('add').call(1, 2)
        #self.assertEqual(3, r)


class PatternMatchTestCase(unittest.TestCase):
    @unittest.skip('Not yet implemented')
    def testSimpleTree(self):
        t = ir.Term('x')
        pat = ir.Binop(ir.Const(2), '+', t)
        res, mp = ir.match_tree(ir.Binop(ir.Const(2), '+', 3), pat)
        self.assertTrue(res)
        self.assertIn(t, mp)
        self.assertEqual(3, mp[t])

    @unittest.skip('Not yet implemented')
    def testSimpleTree2(self):
        t = ir.Term('x')
        t2 = ir.Term('y')
        pat = ir.Binop(ir.Const(2), '+', ir.Binop(t, '-', t2))
        res, mp = ir.match_tree(ir.Binop(ir.Const(2), '+', ir.Binop(2,'-',3)), pat)
        self.assertTrue(res)
        self.assertIn(t, mp)
        self.assertEqual(2, mp[t])
        self.assertIn(t2, mp)
        self.assertEqual(3, mp[t2])
        res, mp = ir.match_tree(ir.Const(2), pat)
        self.assertFalse(res)


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
        v1 = ir.Const(5, 'const', ir.i32)
        self.b.emit(v1)
        v2 = ir.Const(7, 'const', ir.i32)
        self.b.emit(v2)
        v3 = ir.Add(v1, v2, "add", ir.i32)
        self.b.emit(v3)
        self.b.emit(ir.Jump(f.epiloog))
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
        module2 = reader.read(f2)
        f3 = io.StringIO()
        writer.write(module2, f3)
        self.assertEqual(f3.getvalue(), f.getvalue())


class TestReader(unittest.TestCase):
    def testAddExample(self):
        reader = irutils.Reader()
        with open('data/add.pi') as f:
            m = reader.read(f)
            self.assertTrue(m)
            #print(m)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
