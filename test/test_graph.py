#!/usr/bin/python

import unittest
from ppci.utils.graph import Graph, Node, DiGraph, DiNode
from ppci.codegen.interferencegraph import InterferenceGraph
from ppci.codegen.flowgraph import FlowGraph
from ppci.arch.arch import Nop
from ppci.arch.example import Def, Use, DefUse, Add, Cmp, Use3, ExampleRegister


class GraphTestCase(unittest.TestCase):
    """ Test if graph works.
        - Add nodes
        - add edges
        - mask and unmask nodes
        - combine nodes.
    """
    def test_edge(self):
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        g.add_edge(n1, n2)
        self.assertTrue(g.has_edge(n2, n1))
        self.assertTrue(g.has_edge(n1, n2))
        g.del_node(n1)
        g.del_node(n2)

    def test_degree(self):
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        n3 = Node(g)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        self.assertEqual(2, n1.degree)
        self.assertEqual(1, n2.degree)
        g.del_node(n2)
        self.assertEqual(1, n1.degree)

    def test_degree_after_combine(self):
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        n3 = Node(g)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        g.add_edge(n2, n3)
        self.assertEqual(2, n1.degree)
        self.assertEqual(2, n2.degree)
        self.assertEqual(2, n3.degree)
        g.combine(n2, n3)
        self.assertEqual(1, n1.degree)
        self.assertEqual(1, n2.degree)

    def test_degree_with_double_add_edge(self):
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        n3 = Node(g)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        g.add_edge(n1, n3)
        self.assertEqual(2, n1.degree)
        self.assertEqual(1, n2.degree)

    def test_degree_mask_unMask(self):
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        n3 = Node(g)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        self.assertEqual(2, n1.degree)
        self.assertEqual(1, n2.degree)
        g.mask_node(n2)
        g.mask_node(n3)
        self.assertEqual(0, n1.degree)
        g.unmask_node(n2)
        g.unmask_node(n3)
        self.assertEqual(2, n1.degree)

    def test_degree_mask_unmask_combine(self):
        """ Test the combination of masking and combining
            difficult case!
        """
        g = Graph()
        n1 = Node(g)
        n2 = Node(g)
        n3 = Node(g)
        n4 = Node(g)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        g.add_edge(n1, n4)
        g.add_edge(n2, n4)
        self.assertEqual(3, n1.degree)
        g.mask_node(n2)
        g.mask_node(n3)
        g.mask_node(n4)
        self.assertEqual(0, n1.degree)
        g.unmask_node(n3)
        g.combine(n3, n4)
        g.combine(n3, n2)
        self.assertEqual(1, n1.degree)


class DigraphTestCase(unittest.TestCase):
    def test_successor(self):
        g = DiGraph()
        a = DiNode(g)
        b = DiNode(g)
        c = DiNode(g)
        g.add_edge(a, b)
        g.add_edge(b, c)
        self.assertEqual({b}, a.Succ)
        self.assertEqual({b}, c.Pred)
        g.del_node(c)
        self.assertEqual(set(), b.Succ)


class InterferenceGraphTestCase(unittest.TestCase):
    def test_normal_use(self):
        """ Test if interference graph works """
        t1 = ExampleRegister('t1')
        t2 = ExampleRegister('t2')
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        instrs = []
        instrs.append(Def(t1))  # t1 is live
        instrs.append(Def(t2))  # t1, t2 is live
        instrs.append(DefUse(t3, t2))  # t2, t1, t3 live
        instrs.append(DefUse(t4, t1))  # t1, t3, t4 live
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph()
        ig.calculate_interference(cfg)
        self.assertTrue(ig.interfere(t1, t2))
        self.assertFalse(ig.interfere(t2, t4))

    def test_loop_cfg(self):
        """ Test two blocks in a loop
            a:
            t1 = t4
            t2 = 0x10
            jmp b
            b:
            t3 = t2
            t4 = t1
            jmp a

        """
        t1 = ExampleRegister('t1')
        t2 = ExampleRegister('t2')
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        i1 = DefUse(t1, t4)  # t1 is live
        i3 = DefUse(t3, t2)  # t2, t1, t3 live
        i2 = Def(t2, jumps=[i3])  # t1, t2 is live
        i4 = DefUse(t4, t1, jumps=[i1])  # t1, t3, t4 live
        instrs = [i1, i2, i3, i4]
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph()
        ig.calculate_interference(cfg)
        self.assertTrue(ig.interfere(t1, t2))
        self.assertFalse(ig.interfere(t2, t4))

    def test_multiple_successors(self):
        """ Example from wikipedia about liveness """
        a = ExampleRegister('a')
        b = ExampleRegister('b')
        c = ExampleRegister('c')
        d = ExampleRegister('d')
        x = ExampleRegister('x')
        i1 = Def(a)  # a = 3
        i2 = Def(b)  # b = 5
        i3 = Def(d)  # d = 4
        i4 = Def(x)  # x = 100
        i6 = Add(c, a, b)  # c = a + b
        i8 = Def(c)  # c = 4
        i7 = Def(d, jumps=[i8])  # d = 2
        i9 = Use3(b, d, c)  # return b * d + c
        i5 = Cmp(a, b, jumps=[i6, i8])  # if a > b
        instrs = [i1, i2, i3, i4, i5, i6, i7, i8, i9]
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()

        # Get blocks:
        b1 = cfg.get_node(i1)
        b2 = cfg.get_node(i6)
        b3 = cfg.get_node(i8)
        # Should be 3 nodes:
        self.assertEqual(3, len(cfg))

        # Check successors:
        self.assertEqual({b2, b3}, b1.Succ)
        self.assertEqual({b3}, b2.Succ)
        self.assertEqual(set(), b3.Succ)

        # Check predecessors:
        self.assertEqual(set(), b1.Pred)
        self.assertEqual({b1}, b2.Pred)
        self.assertEqual({b2, b1}, b3.Pred)

        # Check block 1:
        self.assertEqual(5, len(b1.instructions))
        self.assertEqual(set(), b1.gen)
        self.assertEqual({a, b, d, x}, b1.kill)

        # Check block 2 gen and killl:
        self.assertEqual(2, len(b2.instructions))
        self.assertEqual({a, b}, b2.gen)
        self.assertEqual({c, d}, b2.kill)

        # Check block 3:
        self.assertEqual(2, len(b3.instructions))
        self.assertEqual({b, d}, b3.gen)
        self.assertEqual({c}, b3.kill)

        # Check block 1 live in and out:
        self.assertEqual(set(), b1.live_in)
        self.assertEqual({a, b, d}, b1.live_out)

        # Check block 2:
        self.assertEqual({a, b}, b2.live_in)
        self.assertEqual({b, d}, b2.live_out)

        # Check block 3:
        self.assertEqual({b, d}, b3.live_in)
        self.assertEqual(set(), b3.live_out)

        # Create interference graph:
        ig = InterferenceGraph()
        ig.calculate_interference(cfg)

    def test_multiple_define_in_loop(self):
        """
            Test if the following works:
            entry:
        I1:  x = 2
        I2:  a = x
        I3:  x = 3
        I4:  b = x
        I5:  c = b
        I6:  cjmp I2, I7
        I7:  nop
        """
        a = ExampleRegister('a')
        b = ExampleRegister('b')
        c = ExampleRegister('c')
        x = ExampleRegister('x')
        i2 = DefUse(a, x)
        i1 = Def(x, jumps=[i2])
        i3 = Def(x)
        i4 = DefUse(b, x)
        i5 = DefUse(c, b)
        i7 = Nop()
        i6 = Nop(jumps=[i2, i7])
        instrs = [i1, i2, i3, i4, i5, i6, i7]
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()

        # Check that there are three nodes:
        self.assertEqual(3, len(cfg))
        self.assertTrue(cfg.has_node(i1))
        self.assertTrue(cfg.has_node(i2))
        self.assertTrue(cfg.has_node(i7))
        # Get block 2:
        b2 = cfg.get_node(i2)

        # Check that block2 has two successors:
        self.assertEqual(2, len(b2.Succ))
        self.assertEqual(2, len(b2.Pred))

        # Check that x is live at end of block 2
        self.assertEqual({x}, b2.live_out)

    def test_loop_variable(self):
        """
            See if a variable defined at input and in block itself
            is marked as live out!
            Probably simpler variant of testMultipleDefineInLoop.
        I1: x = 2
        I2: use x
        I3: x = 3
        I4: jmp I5
        I5: jmp I2
        """
        x = ExampleRegister('x')
        i2 = Use(x)
        i1 = Def(x, jumps=[i2])
        i3 = Def(x)
        i5 = Nop(jumps=[i2])
        i4 = Nop(jumps=[i5])
        self.assertSequenceEqual([x], i1.defined_registers)
        instrs = [i1, i2, i3, i4, i5]
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()

        self.assertEqual(3, len(cfg))
        b1 = cfg.get_node(i1)
        b2 = cfg.get_node(i2)
        b3 = cfg.get_node(i5)
        self.assertEqual(3, len(cfg))
        self.assertEqual({x}, b1.live_out)
        self.assertEqual({x}, b2.live_out)
        self.assertEqual({x}, b3.live_out)

    def test_combine(self):
        t1 = ExampleRegister('t1')
        t2 = ExampleRegister('t2')
        t3 = ExampleRegister('t3')
        t4 = ExampleRegister('t4')
        instrs = []
        instrs.append(Def(t1))
        instrs.append(Def(t2))
        instrs.append(Def(t3))
        instrs.append(DefUse(t4, t3))
        instrs.append(Use(t4))
        instrs.append(Use(t1))
        instrs.append(Use(t2))
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph()
        ig.calculate_interference(cfg)
        ig.combine(ig.get_node(t4), ig.get_node(t3))
        self.assertIs(ig.get_node(t4), ig.get_node(t3))

        # For repr called:
        self.assertTrue(str(ig.get_node(t4)))


if __name__ == '__main__':
    unittest.main()
