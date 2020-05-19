""" Stress test using hypothesis to generate test cases.

Idea:
- generate random graph
- calculate immediate dominators using two different algorithms
- compare the results
"""

from ppci.graph import lt, cfg
from ppci.graph.algorithm import fixed_point_dominator

import hypothesis
from hypothesis_networkx import graph_builder

builder = graph_builder(min_nodes=1, max_nodes=None)


@hypothesis.given(builder)
@hypothesis.settings(max_examples=1000)
def test_a(nx_graph):
    print("nodes", nx_graph.nodes)
    print("edges", nx_graph.edges)

    node_map = {}

    g = cfg.ControlFlowGraph()
    for n in nx_graph.nodes:
        n2 = cfg.ControlFlowNode(g)
        node_map[n] = n2
        g.add_node(n2)

    for n1, n2 in nx_graph.edges:
        g.add_edge(node_map[n1], node_map[n2])

    entry = node_map[0]
    g.entry_node = entry
    g.exit_node = True  # Hack to ensure validate passes ...

    # Algo 1:
    idom1 = lt.calculate_idom(g, entry)
    print("idom1", idom1)

    # Algo 2:
    dom2, sdom2, idom2 = calc_idom2(g, entry)
    print("dom2", dom2)
    print("sdom2", sdom2)
    print("idom2", idom2)

    assert idom1 == idom2

    # Now check properties of nodes:
    for node in g.nodes:
        print(node)
        for other_node in g.nodes:
            dominates = node in dom2[other_node]
            assert dominates == g.dominates(node, other_node)
            strictly_dominates = node in sdom2[other_node]
            assert strictly_dominates == g.strictly_dominates(node, other_node)
    print("BLAAAAAAAAA")


def calc_idom2(g, entry):
    dom2 = fixed_point_dominator.calculate_dominators(g, entry)
    # print('dom2', dom2)
    sdom2 = calc_sdom(g, dom2)
    idom2 = fixed_point_dominator.calculate_immediate_dominators(
        g, dom2, sdom2
    )
    return dom2, sdom2, idom2


def calc_sdom(nodes, _dom):
    _sdom = {}
    for node in nodes:
        if node in _dom:
            _sdom[node] = _dom[node] - {node}
        else:
            _dom[node] = {node}
            _sdom[node] = set()
    return _sdom


if __name__ == "__main__":
    test_a()
    print("OK")
