import unittest
from ppci.irmach import AbstractInstruction as makeIns, Frame, VirtualRegister
from ppci.codegen.registerallocator import RegisterAllocator
from ppci.target import Nop


class RegisterAllocatorTestCase(unittest.TestCase):
    def setUp(self):
        self.ra = RegisterAllocator()

    def testRegAlloc(self):
        f = Frame('tst')
        f.regs = [1, 2,  3, 4, 5, 6]  # for test use numbers!
        f.tempMap = {}
        t1 = VirtualRegister('t1')
        t2 = VirtualRegister('t2')
        t3 = VirtualRegister('t3')
        t4 = VirtualRegister('t4')
        t5 = VirtualRegister('t5')
        f.instructions.append(makeIns(Nop, dst=[t1]))
        f.instructions.append(makeIns(Nop, dst=[t2]))
        f.instructions.append(makeIns(Nop, dst=[t3]))
        f.instructions.append(makeIns(Nop, dst=[t4], src=[t1, t2]))
        f.instructions.append(makeIns(Nop, dst=[t5], src=[t4, t3]))
        f.instructions.append(makeIns(Nop, src=[t5]))
        self.ra.allocFrame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)

    def conflict(self, ta, tb):
        self.assertNotEqual(self.ra.Node(ta).color, self.ra.Node(tb).color)

    def testRegCoalesc(self):
        f = Frame('tst')
        f.regs = [1, 2, 3, 4, 5, 6]  # for test use numbers!
        f.tempMap = {}
        t1 = VirtualRegister('t1')
        t2 = VirtualRegister('t2')
        t3 = VirtualRegister('t3')
        t4 = VirtualRegister('t4')
        t5 = VirtualRegister('t5')
        t6 = VirtualRegister('t6')
        f.instructions.append(makeIns(Nop, dst=[t1]))
        f.instructions.append(makeIns(Nop, dst=[t2]))
        f.instructions.append(makeIns(Nop, dst=[t3]))
        f.instructions.append(makeIns(Nop, dst=[t4], src=[t2, t1]))
        f.instructions.append(makeIns(Nop, dst=[t5], src=[t3]))
        f.instructions.append(makeIns(Nop, dst=[t5], src=[t4, t5]))
        f.instructions.append(makeIns(Nop, dst=[t6], src=[t5]))
        f.instructions.append(makeIns(Nop, src=[t6]))
        self.ra.allocFrame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)
        self.conflict(t1, t3)

if __name__ == '__main__':
    unittest.main()
