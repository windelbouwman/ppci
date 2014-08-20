

class DomTreeBuilder:
    def dominator_tree(f):
        """
            Calculate the dominator tree of this function
        """
        n0 = f.entry

        # Initialize dom map:
        dom = {}
        dom[n0] = {n0}
        N = set(f.Blocks)
        for n in N - {n0}:
            dom[n] = N

        # Run fixed point algorithm:
        change = True
        while change:
            change = False
            for n in N - {n0}:
                # Node n in dominatet by itself and by the intersection of
                # the dominators of its predecessors
                new_dom_n = set.union({n}, set.intersection(*(dom[p] for p in n.Predecessors)))
                if new_dom_n != dom[n]:
                    change = True
                    dom[n] = new_dom_n

        print(dom)

        # Now create dominator tree:
        root = DTreeNode(n0)
        cur = root
        placed = {n0}
        for n in list(N - placed):
            dom[n].remove(n0)
            if (dom[n] - placed) == {n}:
                placed.add(n)
                print('Bingo!', n)

        print(root)
        return dom


class DomBuilder2:
    def lengauer_tarjan(self, f):
        """ Calculate dominators by using 
            T. Lengauer and R. E. Tarjan algorithm from 1979.
        """
        self.n = 0
        self.semi = {}

        self.dfs()

    def dfs(self, vertex):
        n = n + 1
        semi[v] = n
        vertex[n] = v
        for w in v.succ:
            if w not in semi:
                parent[w] = v
                self.dfs(w)
                pred[w].add(v)


class DTreeNode:
    def __init__(self, node):
        self.node = node
        self.children = []

    def add_child(self, tree):
        self.children.append(tree)

    def __repr__(self):
        return "({}={})".format(self.node, self.children)
