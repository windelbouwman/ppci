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
        instrs = []
        instrs.append(AI(Nop, dst=[t1]))
        instrs.append(AI(Nop, dst=[t2]))
        instrs.append(AI(Nop, dst=[t3]))
        cfg = FlowGraph(instrs)
        InterferenceGraph(cfg)

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
        ig = InterferenceGraph(cfg)
        ig.combine(ig.get_node(t4), ig.get_node(t3))
        self.assertIs(ig.get_node(t4), ig.get_node(t3))


if __name__ == '__main__':
    unittest.main()
