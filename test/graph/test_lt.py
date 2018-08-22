""" Test Lengauer Tarjan algorithm """

import unittest
from ppci.graph import DiGraph, DiNode
from ppci.graph.lt import calculate_idom


class LengauerTarjanTestCase(unittest.TestCase):
    """ Test the Lengauer Tarjan algorithm for computing dominators """
    def test_appel_example_19_4(self):
        """ figure 19.4 """
        graph = DiGraph()
        node_1 = DiNode(graph)
        node_2 = DiNode(graph)
        node_3 = DiNode(graph)
        node_4 = DiNode(graph)
        node_5 = DiNode(graph)
        node_6 = DiNode(graph)
        node_7 = DiNode(graph)
        node_1.add_edge(node_2)
        node_2.add_edge(node_3)
        node_2.add_edge(node_4)
        node_3.add_edge(node_5)
        node_3.add_edge(node_6)
        node_5.add_edge(node_7)
        node_6.add_edge(node_7)
        node_7.add_edge(node_2)
        self.assertEqual(7, len(graph))
        idom = calculate_idom(graph, node_1)
        self.assertEqual(7, len(idom))
        correct_idom = {
            node_1: None,
            node_2: node_1,
            node_3: node_2,
            node_4: node_2,
            node_5: node_3,
            node_6: node_3,
            node_7: node_3,
        }
        self.assertEqual(correct_idom, idom)

    def test_appel_example_19_8(self):
        """ figure 19.8 """
        graph = DiGraph()
        node_a = DiNode(graph)
        node_b = DiNode(graph)
        node_c = DiNode(graph)
        node_d = DiNode(graph)
        node_e = DiNode(graph)
        node_f = DiNode(graph)
        node_g = DiNode(graph)
        node_h = DiNode(graph)
        node_i = DiNode(graph)
        node_j = DiNode(graph)
        node_k = DiNode(graph)
        node_l = DiNode(graph)
        node_m = DiNode(graph)
        node_a.add_edge(node_b)
        node_a.add_edge(node_c)
        node_b.add_edge(node_d)
        node_b.add_edge(node_g)
        node_c.add_edge(node_e)
        node_c.add_edge(node_h)
        node_d.add_edge(node_f)
        node_d.add_edge(node_g)
        node_e.add_edge(node_c)
        node_e.add_edge(node_h)
        node_f.add_edge(node_i)
        node_f.add_edge(node_k)
        node_g.add_edge(node_j)
        node_h.add_edge(node_m)
        node_i.add_edge(node_l)
        node_j.add_edge(node_i)
        node_k.add_edge(node_l)
        node_l.add_edge(node_m)
        self.assertEqual(13, len(graph))
        idom = calculate_idom(graph, node_a)
        self.assertEqual(13, len(idom))
        correct_idom = {
            node_a: None,
            node_b: node_a,
            node_c: node_a,
            node_d: node_b,
            node_e: node_c,
            node_f: node_d,
            node_g: node_b,
            node_h: node_c,
            node_i: node_b,
            node_j: node_g,
            node_k: node_f,
            node_l: node_b,
            node_m: node_a,
        }
        self.assertEqual(correct_idom, idom)


if __name__ == '__main__':
    unittest.main()
