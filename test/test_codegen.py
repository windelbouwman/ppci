import unittest
import ppci
from ppci.codegen import CodeGenerator
from ppci import ir
from ppci.target.target_list import thumb_target
from ppci.binutils.outstream import BinaryOutputStream


def genTestFunction():
    m = ir.Module('tst')
    f = ir.Function('tst')
    m.add_function(f)
    return m, f, f.entry


class testCodeGeneration(unittest.TestCase):
    def setUp(self):
        self.cg = CodeGenerator(thumb_target)

    @unittest.skip('TODO')
    def testFunction(self):
        s = BinaryOutputStream(ppci.objectfile.ObjectFile())
        m, f, bb = genTestFunction()
        bb.addInstruction(ir.Exp(ir.Const(123)))
        bb.addInstruction(ir.Jump(f.epiloog))
        obj = self.cg.generate(m, s)
        self.assertTrue(obj)


class testArmCodeGeneration(unittest.TestCase):
    @unittest.skip('TODO')
    def testStack(self):
        s = BinaryOutputStream(ppci.objectfile.ObjectFile())
        cg = CodeGenerator(thumb_target)
        m, f, bb = genTestFunction()
        bb.addInstruction(ir.Move(ir.Mem(ir.Const(1)), ir.Const(22)))
        bb.addInstruction(ir.Jump(f.epiloog))
        cg.generate(m, s)
        #s.dump()


if __name__ == '__main__':
    unittest.main()
