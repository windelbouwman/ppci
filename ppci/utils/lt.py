
"""
Dominators in graphs are handy informations.

Lengauer and Tarjan developed a fast algorithm to calculate dominators
from a graph.

Algorithm as can be found on page 448 of Appel 
"""


def calculate_idom(graph, entry):
    x = LengauerTarjan()
    x.compute(graph, entry)
    return x.idom


class LengauerTarjan:
    """ The lengauer Tarjan algorithm for calculating dominators """
    def __init__(self):
        # Filled during dfs:
        self.N = 0
        self.dfnum = {}
        self.vertex = []
        self.parent = {}

        # Filled later:
        self.ancestor = {}
        self.semi = {}
        self.idom = {}
        self.samedom = {}

    def compute(self, graph, entry):
        bucket = {}
        # Fill maps:
        for n in graph:
            self.semi[n] = None
            self.ancestor[n] = None
            self.idom[n] = None
            self.samedom[n] = None
            bucket[n] = set()

        # Step 1: calculate semi dominators
        self.dfs(None, entry)

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

    def dfs(self, p, node):
        """ Depth first search nodes """
        if node not in self.dfnum:
            self.dfnum[node] = self.N
            self.vertex.append(node)
            self.parent[node] = p
            self.N += 1
            for s in node.successors:
                self.dfs(node, s)

    def link(self, p, n):
        """ Mark p as parent from n """
        self.ancestor[n] = p

    def ancestor_with_lowest_semi(self, v):
        u = v
        while self.ancestor[v]:
            if self.dfnum[self.semi[v]] < self.dfnum[self.semi[u]]:
                u = v
            v = self.ancestor[v]
        return u
