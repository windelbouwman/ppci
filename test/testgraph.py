#!/usr/bin/python

import unittest
from ppci.codegen.graph import Graph, Node, DiGraph, DiNode
from ppci.codegen.interferencegraph import InterferenceGraph
from ppci.codegen.flowgraph import FlowGraph
from ppci import ir
from ppci.irmach import AbstractInstruction as AI, VirtualRegister
from ppci.target import Nop


class GraphTestCase(unittest.TestCase):
    def testEdge(self):
        g = Graph()
        n1 = Node(g)
        g.add_node(n1)
        n2 = Node(g)
        g.add_node(n2)
        g.add_edge(n1, n2)
        self.assertTrue(g.has_edge(n2, n1))
        self.assertTrue(g.has_edge(n1, n2))
        g.del_node(n1)
        g.del_node(n2)

    def testDegree(self):
        g = Graph()
        n1 = Node(g)
        g.add_node(n1)
        n2 = Node(g)
        g.add_node(n2)
        n3 = Node(g)
        g.add_node(n3)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)
        self.assertEqual(2, n1.Degree)
        self.assertEqual(1, n2.Degree)
        g.del_node(n2)
        self.assertEqual(1, n1.Degree)


class DigraphTestCase(unittest.TestCase):
    def testSuccessor(self):
        g = DiGraph()
        a = DiNode(g)
        b = DiNode(g)
        c = DiNode(g)
        g.add_node(a)
        g.add_node(b)
        g.add_node(c)
        g.add_edge(a, b)
        g.add_edge(b, c)
        self.assertEqual({b}, a.Succ)
        self.assertEqual({b}, c.Pred)
        g.del_node(c)
        self.assertEqual(set(), b.Succ)


class InterferenceGraphTestCase(unittest.TestCase):
    def testNormalUse(self):
        """ Test if interference graph works """
        t1 = VirtualRegister('t1')
        t2 = VirtualRegister('t2')
        t3 = VirtualRegister('t3')
        t4 = VirtualRegister('t4')
        instrs = []
        instrs.append(AI(Nop, dst=[t1]))  # t1 is live
        instrs.append(AI(Nop, dst=[t2]))  # t1, t2 is live
        instrs.append(AI(Nop, src=[t2], dst=[t3]))  # t2, t1, t3 live
        instrs.append(AI(Nop, src=[t1], dst=[t4]))  # t1, t3, t4 live
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph(cfg)
        self.assertTrue(ig.interfere(t1, t2))
        self.assertFalse(ig.interfere(t2, t4))

    def testLoopCfg(self):
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
        t1 = VirtualRegister('t1')
        t2 = VirtualRegister('t2')
        t3 = VirtualRegister('t3')
        t4 = VirtualRegister('t4')
        i1 = AI(Nop, dst=[t1], src=[t4])  # t1 is live
        i3 = AI(Nop, src=[t2], dst=[t3])  # t2, t1, t3 live
        i2 = AI(Nop, dst=[t2], jumps=[i3])  # t1, t2 is live
        i4 = AI(Nop, src=[t1], dst=[t4], jumps=[i1])  # t1, t3, t4 live
        instrs = [i1, i2, i3, i4]
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph(cfg)
        self.assertTrue(ig.interfere(t1, t2))
        self.assertFalse(ig.interfere(t2, t4))

    def testMultipleSuccessors(self):
        """ Example from wikipedia about liveness """
        a = VirtualRegister('a')
        b = VirtualRegister('b')
        c = VirtualRegister('c')
        d = VirtualRegister('d')
        x = VirtualRegister('x')
        i1 = AI(Nop, dst=[a])  # a = 3
        i2 = AI(Nop, dst=[b])  # b = 5
        i3 = AI(Nop, dst=[d])  # d = 4
        i4 = AI(Nop, dst=[x])  # x = 100
        i6 = AI(Nop, dst=[c], src=[a, b])  # c = a + b
        i7 = AI(Nop, dst=[d])  # d = 2
        i8 = AI(Nop, dst=[c])  # c = 4
        i9 = AI(Nop, src=[b, d, c])  # return b * d + c
        i5 = AI(Nop, src=[a, b], jumps=[i6, i8])  # if a > b
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
        ig = InterferenceGraph(cfg)

    def testCombine(self):
        t1 = VirtualRegister('t1')
        t2 = VirtualRegister('t2')
        t3 = VirtualRegister('t3')
        t4 = VirtualRegister('t4')
        instrs = []
        instrs.append(AI(Nop, dst=[t1]))
        instrs.append(AI(Nop, dst=[t2]))
        instrs.append(AI(Nop, dst=[t3]))
        instrs.append(AI(Nop, dst=[t4], src=[t3]))
        instrs.append(AI(Nop, src=[t4]))
        instrs.append(AI(Nop, src=[t1]))
        instrs.append(AI(Nop, src=[t2]))
        cfg = FlowGraph(instrs)
        cfg.calculate_liveness()
        ig = InterferenceGraph(cfg)
        ig.combine(ig.get_node(t4), ig.get_node(t3))
        self.assertIs(ig.get_node(t4), ig.get_node(t3))


if __name__ == '__main__':
    unittest.main()
