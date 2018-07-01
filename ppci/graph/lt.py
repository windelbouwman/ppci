"""
Dominators in graphs are handy informations.

Lengauer and Tarjan developed a fast algorithm to calculate dominators
from a graph.

Algorithm as can be found on page 448 of Appel.
"""

import logging
from .digraph import dfs


logger = logging.getLogger('lt')


def calculate_idom(graph, entry, reverse=False):
    x = LengauerTarjan(reverse)
    x.compute(graph, entry)
    return x.idom


class LengauerTarjan:
    """ The lengauer Tarjan algorithm for calculating dominators """
    def __init__(self, reverse):
        self._reverse = reverse

        # Filled during dfs:
        self.N = 0
        self.dfnum = {}
        self.vertex = []
        self.parent = {}

        # Filled later:
        self.ancestor = {}
        self.best = {}
        self.semi = {}
        self.idom = {}
        self.samedom = {}

    def compute(self, graph, entry):
        logger.debug('Computing dominator tree from %s nodes', len(graph))
        bucket = {}
        # Fill maps:
        for n in graph:
            self.semi[n] = None
            self.ancestor[n] = None
            self.idom[n] = None
            self.samedom[n] = None
            bucket[n] = set()

        # Step 1: calculate semi dominators
        self.dfs(entry)

        # Loop over nodes in reversed dfs order:
        for n in reversed(self.vertex[1:]):
            p = self.parent[n]

            # Determine semi dominator for n:
            candidates = []
            for v in n.predecessors:
                if self.dfnum[v] <= self.dfnum[n]:
                    s2 = v
                else:
                    s2 = self.semi[self.ancestor_with_lowest_semi(v)]
                candidates.append(s2)

            # Select semi-dominator from candidates:
            assert candidates
            s = min(candidates, key=lambda x: self.dfnum[x])
            self.semi[n] = s
            bucket[s].add(n)

            # Link:
            self.link(p, n)

            for v in bucket[p]:
                y = self.ancestor_with_lowest_semi(v)
                if self.semi[y] is self.semi[v]:
                    self.idom[v] = p
                else:
                    self.samedom[v] = y
            bucket[p].clear()

        for n in self.vertex:
            if self.samedom[n]:
                self.idom[n] = self.idom[self.samedom[n]]
        return self.idom

    def dfs(self, start_node):
        """ Depth first search nodes """
        for parent, node in dfs(start_node):
            assert node not in self.dfnum
            self.dfnum[node] = self.N
            self.vertex.append(node)
            self.parent[node] = parent
            self.N += 1

    def link(self, p, n):
        """ Mark p as parent from n """
        self.ancestor[n] = p
        self.best[n] = n

    def ancestor_with_lowest_semi(self, v):
        # TODO: this is a slow algorithm, path compression can help
        # to increase the speed.
        u = v
        while self.ancestor[v]:
            if self.dfnum[self.semi[v]] < self.dfnum[self.semi[u]]:
                u = v

            # Traverse upwards:
            v = self.ancestor[v]
        return u

    def ancestor_with_lowest_semi_new(self, v):
        """ Modified algorithm. Sort of with path compression. """
        raise NotImplementedError('appears to have a bug?')
        x = v
        while self.ancestor[x]:
            if self.dfnum[self.semi[x]] < self.dfnum[self.semi[self.best[v]]]:
                self.best[v] = x
            self.ancestor[v] = self.ancestor[x]

            # Iterate:
            x = self.ancestor[x]
        return self.best[v]

    def ancestor_with_lowest_semi_fast(self, v):
        """ The O(log N) implementation """
        # TODO: this version suffers from a recursion limit
        a = self.ancestor[v]
        if self.ancestor[a]:
            b = self.ancestor_with_lowest_semi(a)
            self.ancestor[v] = self.ancestor[a]
            if self.dfnum[self.semi[b]] < self.dfnum[self.semi[self.best[v]]]:
                self.best[v] = b
        return self.best[v]
