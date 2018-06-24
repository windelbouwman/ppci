""" Directed graph.

In a directed graph, the edges have a direction.
"""

from collections import defaultdict
from .graph import BaseGraph, Node


class DiGraph(BaseGraph):
    """ Directed graph. """
    def __init__(self):
        super().__init__()
        self.suc_map = defaultdict(set)
        self.pre_map = defaultdict(set)

    def del_node(self, node):
        """ Remove a node from the graph """
        s = list(self.successors(node))
        for m in s:
            self.del_edge(node, m)

        p = list(self.predecessors(node))
        for m in p:
            self.del_edge(m, node)
        self.nodes.remove(node)

    def add_edge(self, n, m):
        """ Add a directed edge from n to m """
        assert n in self.nodes
        assert m in self.nodes
        if not self.has_edge(n, m):
            self.suc_map[n].add(m)
            self.pre_map[m].add(n)
            self.adj_map[n].add(m)
            self.adj_map[m].add(n)

    def del_edge(self, n, m):
        """ Delete a directed edge """
        assert n != m
        assert n in self.nodes
        assert m in self.nodes
        if self.has_edge(n, m):
            self.suc_map[n].remove(m)
            self.pre_map[m].remove(n)
            self.adj_map[m].remove(n)
            self.adj_map[n].remove(m)

    def has_edge(self, n, m):
        """ Test if there exist and edge between n and m """
        return m in self.suc_map[n]

    def successors(self, node):
        """ Get the successors of the node """
        return self.suc_map[node]

    def predecessors(self, node):
        """ Get the predecessors of the node """
        return self.pre_map[node]


class DiNode(Node):
    """ Node in a directed graph """
    @property
    def successors(self):
        """ Get the successors of this node """
        return self.graph.successors(self)

    @property
    def predecessors(self):
        """ Get the predecessors of this node """
        return self.graph.predecessors(self)


def dfs(start_node, reverse=False):
    """ Visit nodes in depth-first-search order.

    Args:
        - start_node: node to start with
        - reverse: traverse the graph by reversing the edge directions.
    """
    visited = set()
    worklist = [(None, start_node)]
    while worklist:
        parent, node = worklist.pop()
        if node not in visited:
            visited.add(node)
            yield parent, node
            if reverse:
                for predecessor in node.predecessors:
                    worklist.append((node, predecessor))
            else:
                for successor in node.successors:
                    worklist.append((node, successor))
