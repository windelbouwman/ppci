""" Directed graph.

In a directed graph, the edges have a direction.
"""

from collections import defaultdict
from .graph import Graph, Node


class DiGraph(Graph):
    """ Directed graph. """
    def __init__(self):
        super().__init__()
        self.suc_map = defaultdict(set)
        self.pre_map = defaultdict(set)

    def add_edge(self, n, m):
        """ Add a directed edge from n to m """
        assert n in self.nodes
        assert m in self.nodes
        if (n, m) not in self.edges:
            self.edges.add((n, m))
            self.suc_map[n].add(m)
            self.pre_map[m].add(n)
            self.adj_map[n].add(m)
            self.adj_map[m].add(n)
            self.degree_map[m] += 1
            self.degree_map[n] += 1

    def successors(self, n):
        """ Get the successors of the node """
        return self.suc_map[n] & self.nodes

    def predecessors(self, n):
        """ Get the predecessors of the node """
        return self.pre_map[n] & self.nodes


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
