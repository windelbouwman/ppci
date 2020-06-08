"""
Dominators in graphs are handy informations.

Lengauer and Tarjan developed a fast algorithm to calculate dominators
from a graph.

Algorithm 19.9 and 19.10 as can be found on page 448 of Appel.
"""

import logging
from .digraph import dfs


logger = logging.getLogger("lt")


def calculate_idom(graph, entry, reverse=False):
    x = LengauerTarjan(reverse)
    return x.compute(graph, entry)


class LengauerTarjan:
    """ The lengauer Tarjan algorithm for calculating dominators """

    def __init__(self, reverse):
        self._reverse = reverse

        # Filled during dfs:
        self.dfnum = {}  # depth-first number
        self.vertex = []  # Linear list of nodes
        self.parent = {}

        # Filled later:
        self.ancestor = {}
        self.best = {}
        self.semi = {}

    def compute(self, graph, entry):
        logger.debug("Computing dominator tree from %s nodes", len(graph))
        bucket = {}

        # Fill maps:
        for n in graph:
            bucket[n] = set()

        # Step 1: calculate semi dominators
        self.dfs(entry)

        idom = {}
        samedom = {}

        # Loop over nodes in reversed dfs order:
        for n in reversed(self.vertex[1:]):
            p = self.parent[n]

            # Determine semi dominator for n:
            s = p
            for v in n.predecessors:
                if self.dfnum[v] <= self.dfnum[n]:
                    s2 = v
                else:
                    s2 = self.semi[self.ancestor_with_lowest_semi(v)]
                assert s2 is not None

                # Select candidate with lowest dfnum:
                if self.dfnum[s2] < self.dfnum[s]:
                    s = s2

            assert n not in self.semi
            self.semi[n] = s
            bucket[s].add(n)

            self.link(p, n)

            for v in bucket[p]:
                y = self.ancestor_with_lowest_semi(v)
                if self.semi[y] is self.semi[v]:
                    idom[v] = p
                else:
                    samedom[v] = y
            bucket[p].clear()

        for n in self.vertex[1:]:
            if n in samedom:
                idom[n] = idom[samedom[n]]
            else:
                assert n in idom
        return idom

    def dfs(self, start_node):
        """ Depth first search nodes """
        for dfnum, pair in enumerate(dfs(start_node)):
            parent, node = pair
            assert node not in self.dfnum
            self.dfnum[node] = dfnum
            assert node not in self.parent
            self.parent[node] = parent
            self.vertex.append(node)

    def link(self, p, n):
        """ Mark p as parent from n """
        assert n not in self.ancestor
        self.ancestor[n] = p
        self.best[n] = n

    def ancestor_with_lowest_semi_naive(self, v):
        """ O(N^2) implementation.

        This is a slow algorithm, path compression can be used
        to increase speed.
        """
        u = v
        while v in self.ancestor:
            if self.dfnum[self.semi[v]] < self.dfnum[self.semi[u]]:
                u = v

            # Traverse upwards:
            v = self.ancestor[v]
        return u

    def ancestor_with_lowest_semi(self, v):
        """ O(log N) implementation with path compression.

        Rewritten from recursive function to prevent hitting the
        recursion limit for large graphs.
        """
        original_v = v

        # Traverse to highest parent
        path = []
        a = self.ancestor[v]
        while a in self.ancestor:
            path.append((v, a))
            v = a
            a = self.ancestor[v]

        # traverse back to v:
        for v, a in reversed(path):
            b = self.best[a]
            self.ancestor[v] = self.ancestor[a]
            if self.dfnum[self.semi[b]] < self.dfnum[self.semi[self.best[v]]]:
                self.best[v] = b

        return self.best[original_v]

    def ancestor_with_lowest_semi_fast(self, v):
        """ The O(log N) implementation with path compression.

        This version suffers from a recursion limit for large graphs.
        """
        a = self.ancestor[v]
        if a in self.ancestor:
            b = self.ancestor_with_lowest_semi(a)
            self.ancestor[v] = self.ancestor[a]
            if self.dfnum[self.semi[b]] < self.dfnum[self.semi[self.best[v]]]:
                self.best[v] = b
        return self.best[v]
