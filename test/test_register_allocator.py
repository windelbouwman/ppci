import unittest
from ppci.codegen.registerallocator import GraphColoringRegisterAllocator
from ppci.api import get_arch
from ppci.arch.arch import Frame
from ppci.arch.example import Def, Use, Add, Mov, R0, R1, ExampleRegister
from ppci.arch.example import R10, R10l, DefHalf, UseHalf
from ppci.binutils.debuginfo import DebugDb

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock


class GraphColoringRegisterAllocatorTestCase(unittest.TestCase):
    """ Use the example target to test the different cases of the register
        allocator.
        Possible cases: freeze of move, spill of register
    """
    def setUp(self):
        arch = get_arch('example')
        debug_db = DebugDb()
        self.register_allocator = GraphColoringRegisterAllocator(
            arch, None, debug_db)

    def conflict(self, ta, tb):
        reg_a = self.register_allocator.node(ta).reg
        reg_b = self.register_allocator.node(tb).reg
        self.assertNotEqual(reg_a, reg_b)

    def test_register_allocation(self):
        f = Frame('tst', [], [], None, [])
        t1 = ExampleRegister('t1')
        t2 = ExampleRegister('t2')
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        t5 = ExampleRegister('t5')
        f.instructions.append(Def(t1))
        f.instructions.append(Def(t2))
        f.instructions.append(Def(t3))
        f.instructions.append(Add(t4, t1, t2))
        f.instructions.append(Add(t5, t4, t3))
        f.instructions.append(Use(t5))
        self.register_allocator.alloc_frame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)

    def test_register_coalescing(self):
        """ Register coalescing happens when a move can be eliminated """
        f = Frame('tst', [], [], None, [])
        t1 = ExampleRegister('t1')
        t2 = ExampleRegister('t2')
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        t5 = ExampleRegister('t5')
        t6 = ExampleRegister('t6')
        f.instructions.append(Def(t1))
        f.instructions.append(Def(t2))
        f.instructions.append(Def(t3))
        f.instructions.append(Add(t4, t2, t1))
        f.instructions.append(Mov(t5, t3))
        f.instructions.append(Add(t5, t4, t5))
        f.instructions.append(Mov(t6, t5))
        f.instructions.append(Use(t6))
        self.register_allocator.alloc_frame(f)
        self.conflict(t1, t2)
        self.conflict(t2, t3)
        self.conflict(t1, t3)

    def test_constrained_move(self):
        """ Test a constrained move.

            Do this by creating two pre-colored registers. Move one
            and add the other with the copy of the first.

            The move can then not be coalesced, and will be frozen.
        """
        f = Frame('tst', [], [], None, [])
        t1 = R0
        t2 = R0
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        f.instructions.append(Def(t1))
        move = Mov(t3, t1, ismove=True)
        f.instructions.append(move)
        f.instructions.append(Def(t2))
        f.instructions.append(Add(t4, t2, t3))
        f.instructions.append(Use(t4))
        self.register_allocator.alloc_frame(f)

        # Check t1 and t2 are pre-colored:
        self.assertEqual(
            {self.register_allocator.node(R0)},
            self.register_allocator.precolored)
        self.assertEqual(set(), self.register_allocator.coalescedMoves)
        self.assertEqual({move}, self.register_allocator.constrainedMoves)
        self.conflict(t2, t3)
        self.assertEqual(set(), self.register_allocator.frozenMoves)
        self.assertIn(move, f.instructions)

    def test_constrained_move_by_alias(self):
        """ Test if aliased registers work and cannot be coalesced. """
        f = Frame('tst', [], [], None, [])
        t1 = R10
        t2 = R10l
        t3 = ExampleRegister('t3')
        move = Mov(t3, t1, ismove=True)
        f.instructions.append(Def(t1))
        f.instructions.append(move)
        f.instructions.append(DefHalf(t2))
        f.instructions.append(UseHalf(t2))
        f.instructions.append(Use(t3))
        self.register_allocator.alloc_frame(f)

        # Check t1 and t2 are pre-colored:
        self.assertEqual(
            {self.register_allocator.node(R10),
             self.register_allocator.node(R10l)},
            self.register_allocator.precolored)
        self.assertEqual(set(), self.register_allocator.coalescedMoves)
        self.assertEqual({move}, self.register_allocator.constrainedMoves)
        self.conflict(t2, t3)
        self.assertEqual(set(), self.register_allocator.frozenMoves)
        self.assertIn(move, f.instructions)

    def test_freeze(self):
        """ Create a situation where no select and no coalesc is possible
        """
        f = Frame('tst', [], [], None, [])
        t4 = ExampleRegister('t4')
        t5 = ExampleRegister('t5')
        f.instructions.append(Def(R0))
        move = Mov(R1, R0, ismove=True)
        f.instructions.append(move)
        f.instructions.append(Def(t4))
        f.instructions.append(Add(t5, t4, R1))
        f.instructions.append(Use(t5))
        self.register_allocator.alloc_frame(f)

        self.assertEqual(set(), self.register_allocator.coalescedMoves)
        # self.assertEqual({move}, self.register_allocator.frozenMoves)
        self.conflict(R1, R0)

    def test_spill(self):
        pass

    # @patch('ppci.codegen.interferencegraph.InterferenceGraph')
    def test_init_data(self):  # , ig):
        frame = MagicMock()
        # frame.configure
        self.register_allocator.init_data(frame)
        # print(frame.mock_calls)
        # self.assertEqual(1, len(self.register_allocator.precolored))

    def test_coalesc(self):
        pass
        # self.register_allocator.coalesc()

if __name__ == '__main__':
    unittest.main()
