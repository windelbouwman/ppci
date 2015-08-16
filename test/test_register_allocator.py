import unittest
from ppci.codegen.registerallocator import RegisterAllocator
from ppci.target.isa import Register
from ppci.target.target import Frame
from ppci.target.example import Def, Use, Add, Mov, R0, R1


class RegisterAllocatorTestCase(unittest.TestCase):
    """ Use the example target to test the different cases of the register
        allocator.
        Possible cases: freeze of move, spill of register
    """
    def setUp(self):
        self.ra = RegisterAllocator()

    def conflict(self, ta, tb):
        self.assertNotEqual(self.ra.Node(ta).color, self.ra.Node(tb).color)

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
        self.ra.alloc_frame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)

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
        self.ra.alloc_frame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)
        self.conflict(t1, t3)

    def test_constrained_move(self):
        """ Test a constrained move.

            Do this by creating two pre-colored registers. Move one
            and add the other with the copy of the first.

            The move can then not be coalesced, and will be frozen.
        """
        f = Frame('tst')
        t1 = R0
        t2 = R0
        t3 = Register('t3')
        t4 = Register('t4')
        f.regs = [Register('R{}'.format(v), v) for v in range(3)]
        f.instructions.append(Def(t1))
        move = Mov(t3, t1, ismove=True)
        f.instructions.append(move)
        f.instructions.append(Def(t2))
        f.instructions.append(Add(t4, t2, t3))
        f.instructions.append(Use(t4))
        self.ra.alloc_frame(f)

        # Check t1 and t2 are pre-colored:
        self.assertEqual({self.ra.Node(R0)}, self.ra.precolored)
        self.assertEqual(set(), self.ra.coalescedMoves)
        self.assertEqual({move}, self.ra.constrainedMoves)
        self.conflict(t2, t3)
        self.assertEqual(set(), self.ra.frozenMoves)
        self.assertIn(move, f.instructions)

    def test_freeze(self):
        """ Create a situation where no select and no coalesc is possible
        """
        f = Frame('tst')
        t1 = Register('t1')
        t2 = Register('t2')
        t3 = Register('t3')
        t4 = Register('t4')
        t5 = Register('t5')
        t6 = Register('t6')
        f.regs = [Register('R{}'.format(v), v) for v in range(3)]
        f.instructions.append(Def(R0))
        move = Mov(R1, R0, ismove=True)
        f.instructions.append(move)
        f.instructions.append(Def(t4))
        f.instructions.append(Add(t5, t4, R1))
        f.instructions.append(Use(t5))
        self.ra.alloc_frame(f)

        self.assertEqual(set(), self.ra.coalescedMoves)
        #self.assertEqual({move}, self.ra.frozenMoves)
        self.conflict(R1, R0)

    def test_spill(self):
        pass


if __name__ == '__main__':
    unittest.main()
