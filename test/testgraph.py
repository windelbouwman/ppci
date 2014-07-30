#!/usr/bin/python

import unittest
from ppci.codegen.graph import Graph, Node, DiGraph, DiNode
from ppci.codegen.interferencegraph import InterferenceGraph
from ppci.codegen.flowgraph import FlowGraph
from ppci import ir
from ppci.irmach import AbstractInstruction as AI
from ppci.target import Nop


class GraphTestCase(unittest.TestCase):
    def testEdge(self):
        g = Graph()
        n1 = Node(g)
        g.add_node(n1)
        n2 = Node(g)
        g.add_node(n2)
        g.addEdge(n1, n2)
        self.assertTrue(g.hasEdge(n2, n1))
        self.assertTrue(g.hasEdge(n1, n2))
        g.delNode(n1)
        g.delNode(n2)

    def testDegree(self):
        g = Graph()
        n1 = Node(g)
        g.add_node(n1)
        n2 = Node(g)
        g.add_node(n2)
        n3 = Node(g)
        g.add_node(n3)
        g.addEdge(n1, n2)
        g.addEdge(n1, n3)
        self.assertEqual(2, n1.Degree)
        self.assertEqual(1, n2.Degree)
        g.delNode(n2)
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
        g.addEdge(a, b)
        g.addEdge(b, c)
        self.assertEqual({b}, a.Succ)
        self.assertEqual({b}, c.Pred)
        g.delNode(c)
        self.assertEqual(set(), b.Succ)


class InterferenceGraphTestCase(unittest.TestCase):
    def testNormalUse(self):
        t1 = ir.Temp('t1')
        t2 = ir.Temp('t2')
        t3 = ir.Temp('t3')
        t4 = ir.Temp('t4')
        t5 = ir.Temp('t5')
        t6 = ir.Temp('t6')
        instrs = []
        instrs.append(AI(Nop, dst=[t1]))
        instrs.append(AI(Nop, dst=[t2]))
        instrs.append(AI(Nop, dst=[t3]))
        cfg = FlowGraph(instrs)
        ig = InterferenceGraph(cfg)

    def testCombine(self):
        t1 = ir.Temp('t1')
        t2 = ir.Temp('t2')
        t3 = ir.Temp('t3')
        t4 = ir.Temp('t4')
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
        ig.Combine(ig.getNode(t4), ig.getNode(t3))
        self.assertIs(ig.getNode(t4), ig.getNode(t3))


if __name__ == '__main__':
    unittest.main()
