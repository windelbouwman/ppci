import unittest
from ppci.codegen.registerallocator import RegisterAllocator
from ppci.target import Register, Frame
from ppci.target.example import Def, Use, Add, Mov


class RegisterAllocatorTestCase(unittest.TestCase):
    def setUp(self):
        self.ra = RegisterAllocator()

    def test_register_allocation(self):
        f = Frame('tst')
        t1 = Register('t1')
        t2 = Register('t2')
        t3 = Register('t3')
        t4 = Register('t4')
        t5 = Register('t5')
        f.regs = [Register('t{}'.format(v), v) for v in range(7)]
        f.instructions.append(Def(t1))
        f.instructions.append(Def(t2))
        f.instructions.append(Def(t3))
        f.instructions.append(Add(t4, t1, t2))
        f.instructions.append(Add(t5, t4, t3))
        f.instructions.append(Use(t5))
        self.ra.allocFrame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)

    def conflict(self, ta, tb):
        self.assertNotEqual(self.ra.Node(ta).color, self.ra.Node(tb).color)

    def test_register_coalescing(self):
        """ Register coalescing happens when a move can be eliminated """
        f = Frame('tst')
        t1 = Register('t1')
        t2 = Register('t2')
        t3 = Register('t3')
        t4 = Register('t4')
        t5 = Register('t5')
        t6 = Register('t6')
        f.regs = [Register('t{}'.format(v), v) for v in range(7)]
        f.instructions.append(Def(t1))
        f.instructions.append(Def(t2))
        f.instructions.append(Def(t3))
        f.instructions.append(Add(t4, t2, t1))
        f.instructions.append(Mov(t5, t3))
        f.instructions.append(Add(t5, t4, t5))
        f.instructions.append(Mov(t6, t5))
        f.instructions.append(Use(t6))
        self.ra.allocFrame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)
        self.conflict(t1, t3)


if __name__ == '__main__':
    unittest.main()
