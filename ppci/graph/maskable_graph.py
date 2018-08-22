""" Graph type that supports temporary removal of nodes.

Edge information is retained, and restored when the node is placed back.
"""
from itertools import chain
from collections import defaultdict
from .graph import Graph
from ..utils.collections import OrderedSet


class MaskableGraph(Graph):
    """ A graph that allows masking nodes temporarily """
    def __init__(self):
        super().__init__()
        self._masked_nodes = set()
        self._masked_adj = defaultdict(OrderedSet)

    def mask_node(self, node):
        """ Add the node into the masked set """
        assert not self.is_masked(node)
        self._masked_nodes.add(node)

        # Update neighbour adjecency:
        for neighbour in chain(self.adj_map[node], self._masked_adj[node]):
            self.adj_map[neighbour].remove(node)
            self._masked_adj[neighbour].add(node)

        self.nodes.remove(node)

    def unmask_node(self, node):
        """ Unmask a node (put it back into the graph """
        assert self.is_masked(node)
        self._masked_nodes.remove(node)
        self.nodes.add(node)

        # Restore connections:
        for neighbour in chain(self.adj_map[node], self._masked_adj[node]):
            self.adj_map[neighbour].add(node)
            self._masked_adj[neighbour].remove(node)

    def is_masked(self, node):
        """ Test if a node is masked """
        return node in self._masked_nodes

    def combine(self, n, m):
        """ Merge nodes n and m into node n """
        assert n != m
        # assert not self.has_edge(n, m)
        # if self.has_edge(n, m):
        #    self.degree_map[n] += 1

        # node m is going away, make sure to unmask it first:
        if self.is_masked(m):
            self.unmask_node(m)

        # Move stored masked edges:
        for neighbour in list(self._masked_adj[m]):
            # Move connection end 1:
            self.adj_map[neighbour].remove(m)
            self.adj_map[neighbour].add(n)

            # Move connection end 2:
            self._masked_adj[m].remove(neighbour)
            self._masked_adj[n].add(neighbour)

        assert len(self._masked_adj[m]) == 0

        assert not self.is_masked(n), 'Combining only allowed for non-masked'
        super().combine(n, m)
