
from collections import namedtuple

DomTreeNode = namedtuple('DomTreeNode', ['block', 'children'])


class CfgInfo:
    """ Calculate control flow graph info, such as dominators
    dominator tree and dominance frontier """
    def __init__(self, function):
        # Store ir related info:
        self.function = function
        self.n0 = function.entry
        blocks = function.calc_reachable_blocks()
        self.N = blocks

        self.pred = {}
        self.succ = {}
        for block in blocks:
            self.prepare(block)

        # From here only succ and pred are relevant:
        self.dom = {}
        self.sdom = {}
        self.calculate_dominators()

        self.idom = {}
        self.calculate_idom()

        self.df = {}
        self.calculate_df()

    def __repr__(self):
        return 'CfgInfo(pred={}\n, succ={}\n, dom={}\n)'.format(
            self.pred, self.succ, self.dom)

    def prepare(self, block):
        self.pred[block] = set(block.predecessors) & self.N
        self.succ[block] = set(block.successors) & self.N

    def calculate_dominators(self):
        """
            Calculate the dominator sets iteratively
        """

        # Initialize dom map:
        self.dom[self.n0] = {self.n0}
        for n in self.N - {self.n0}:
            self.dom[n] = self.N

        # Run fixed point algorithm:
        change = True
        while change:
            change = False
            for n in self.N - {self.n0}:
                # Node n in dominatet by itself and by the intersection of
                # the dominators of its predecessors
                pred_doms = list(self.dom[p] for p in self.pred[n])
                if not pred_doms:  # pragma: no cover
                    # We cannot be here!
                    # Always add entry as a predecessor of epilog to prevent
                    # this situation.
                    print(self.pred[n], n)
                    print(pred_doms)
                    raise Exception()
                new_dom_n = set.union({n}, set.intersection(*pred_doms))
                if new_dom_n != self.dom[n]:
                    change = True
                    self.dom[n] = new_dom_n

        # Calculate the strict dominators:
        for n in self.N - {self.n0}:
            self.sdom[n] = self.dom[n] - {n}

    def strictly_dominates(self, n1, n2):
        """ Calculate if n1 strictly dominates n2 """
        return n1 in self.sdom[n2]

    def calculate_idom(self):
        """
            Calculate immediate dominator by choosing n from sdom(x) such
            that dom(n) == sdom(x)
        """
        for n in list(self.N - {self.n0}):
            for x in self.sdom[n]:
                if self.dom[x] == self.sdom[n]:
                    # This must be the only definition of idom:
                    assert n not in self.idom
                    self.idom[n] = x

        # Create a tree:
        self.tree_map = {}
        for n in self.N:
            self.tree_map[n] = DomTreeNode(n, list())

        # Add all nodes except for the root node into the tree:
        for n in self.N - {self.n0}:
            parent = self.tree_map[self.idom[n]]
            node = self.tree_map[n]
            parent.children.append(node)
        self.root_tree = self.tree_map[self.n0]

    def bottom_up(self, node):
        """ Generator that yields all nodes in bottom up way """
        for c in node.children:
            for cc in self.bottom_up(c):
                yield cc
        yield node.block

    def children(self, n):
        """ Return all children for node n """
        tree = self.tree_map[n]
        for c in tree.children:
            yield c.block

    def calculate_df(self):
        """
            Algorithm from Ron Cytron et al.

            how to calculate the dominance frontier for all nodes using
            the dominator tree.
        """
        for x in self.bottom_up(self.root_tree):
            # Initialize dominance frontier to the empty set:
            self.df[x] = set()
            for y in self.succ[x]:
                if self.idom[y] != x:
                    self.df[x].add(y)   # Local rule for dominance frontier
            for z in self.children(x):
                for y in self.df[z]:
                    if self.idom[y] != x:
                        self.df[x].add(y)  # upwards rule
