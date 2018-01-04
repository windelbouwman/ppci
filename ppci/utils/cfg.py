""" Control flow graph algorithms.

Functions present:

- dominators
- post dominators
- reachability
- dominator tree
- dominance frontier

"""

# TODO: this is possibly the third edition of flow graph code.. Merge at will!
from .graph import DiGraph, DiNode
from collections import namedtuple

DomTreeNode = namedtuple('DomTreeNode', ['node', 'children'])
Loop = namedtuple('Loop', ['header', 'rest'])


def ir_function_to_graph(ir_function):
    """ Take an ir function and create a cfg of it """
    i2c = IrToCfg()
    return i2c.convert(ir_function)


class IrToCfg:
    """ Convert ir function into a control flow graph """
    def __init__(self):
        self.block_map = None

    def convert(self, ir_function):
        """ Convert ir function into a control flow graph """
        self.block_map = {}
        self.cfg = ControlFlowGraph()
        self.cfg.exit_node = self.new_node(None)
        self.cfg.entry_node = self.get_node(ir_function.entry)
        return self.cfg, self.block_map

    def new_node(self, name):
        node = ControlFlowNode(self.cfg, name=name)
        return node

    def get_node(self, block):
        if block in self.block_map:
            return self.block_map[block]
        else:
            # Create a new node:
            node = self.new_node(block.name)
            self.block_map[block] = node

            # Add proper edges:
            if len(block.successors) == 0:
                # Exit or return!
                node.add_edge(self.cfg.exit_node)
            else:
                for successor_block in block.successors:
                    successor_node = self.get_node(successor_block)
                    node.add_edge(successor_node)

                # TODO: hack to store yes and no blocks:
                if len(block.successors) == 2:
                    node.yes = self.get_node(block.last_instruction.lab_yes)
                    node.no = self.get_node(block.last_instruction.lab_no)
            return node


class ControlFlowGraph(DiGraph):
    """ Control flow graph.

    Has methods to query properties of the control flow graph and its nodes.

    Such as:
    - Dominators
    - Strict dominators
    - Immediate dominators
    - Post dominators
    - Strict post dominators
    - Immediate post dominators
    - Reachable nodes
    - Loops
    """
    def __init__(self):
        super().__init__()
        self.entry_node = None
        self.exit_node = None
        self._dom = None  # dominators
        self._sdom = None  # Strict dominators
        self._idom = None  # immediate_dominators
        self._pdom = None  # post dominators
        self._spdom = None  # Strict post dominators
        self._ipdom = None  # post dominators
        self._reach = None  # Reach map
        self.root_tree = None

    def validate(self):
        """ Run some sanity checks on the control flow graph """
        assert self.entry_node
        assert self.exit_node

    def dominates(self, one, other):
        """ Test whether a node dominates another node """
        if self._dom is None:
            self.calculate_dominators()
        return one in self._dom[other]

    def strictly_dominates(self, one, other):
        """ Test whether a node strictly dominates another node """
        if self._sdom is None:
            self.calculate_strict_dominators()
        return one in self._sdom[other]

    def post_dominates(self, one, other):
        """ Test whether a node post dominates another node """
        if self._pdom is None:
            self.calculate_post_dominators()
        return one in self._pdom[other]

    def get_immediate_dominator(self, node):
        """ Retrieve a nodes immediate dominator """
        if self._idom is None:
            self.calculate_immediate_dominators()
        return self._idom[node]

    def get_immediate_post_dominator(self, node):
        """ Retrieve a nodes immediate post dominator """
        if self._ipdom is None:
            self.calculate_immediate_post_dominators()
        return self._ipdom[node]

    def can_reach(self, one, other):
        if self._reach is None:
            self.calculate_reach()
        return other in self._reach[one]

    def calculate_dominators(self):
        """ Calculate the dominator sets iteratively """
        self.validate()

        # Initialize dominator map:
        self._dom = {}
        for node in self.nodes:
            if node is self.entry_node:
                self._dom[node] = {node}
            else:
                self._dom[node] = set(self.nodes)

        # Run fixed point iteration:
        change = True
        while change:
            change = False
            for node in self.nodes:
                # A node is dominated by itself and by the intersection of
                # the dominators of its predecessors
                pred_doms = list(
                    self._dom[p] for p in self.predecessors(node))
                if pred_doms:
                    new_dom_n = set.union({node}, set.intersection(*pred_doms))
                    if new_dom_n != self._dom[node]:
                        change = True
                        self._dom[node] = new_dom_n

    def calculate_post_dominators(self):
        """ Calculate the post dominator sets iteratively.

        Post domination is the same as domination, but then starting at
        the exit node.
        """
        self.validate()

        # Initialize dominator map:
        self._pdom = {}
        for node in self.nodes:
            if node is self.exit_node:
                self._pdom[node] = {node}
            else:
                self._pdom[node] = set(self.nodes)

        # Run fixed point iteration:
        change = True
        while change:
            change = False
            for node in self.nodes:
                # A node is post dominated by itself and by the intersection
                # of the post dominators of its successors
                succ_pdoms = list(
                    self._pdom[s] for s in self.successors(node))
                if succ_pdoms:
                    new_pdom_n = set.union(
                        {node}, set.intersection(*succ_pdoms))
                    if new_pdom_n != self._pdom[node]:
                        change = True
                        self._pdom[node] = new_pdom_n

    def calculate_strict_dominators(self):
        """ Calculate the strict dominators.

        Strict domination is the dominance set minus the node itself.
        """
        if self._dom is None:
            self.calculate_dominators()

        if self._pdom is None:
            self.calculate_post_dominators()

        self._sdom = {}
        self._spdom = {}
        for node in self.nodes:
            self._sdom[node] = self._dom[node] - {node}
            self._spdom[node] = self._pdom[node] - {node}

    def calculate_immediate_dominators(self):
        """ Calculate immediate dominators for all nodes.

        Do this by choosing n from sdom(x) such that dom(n) == sdom(x).
        """
        if self._dom is None:
            self.calculate_dominators()

        if self._sdom is None:
            self.calculate_strict_dominators()

        self._idom = {}

        for node in self.nodes:
            if self._sdom[node]:
                for x in self._sdom[node]:
                    if self._dom[x] == self._sdom[node]:
                        # This must be the only definition of idom:
                        assert node not in self._idom
                        self._idom[node] = x
            else:
                # No strict dominators, hence also no immediate dominator:
                self._idom[node] = None

    def calculate_dominator_tree(self):
        # Create a tree:
        if self._idom is None:
            self.calculate_immediate_dominators()

        self.tree_map = {}
        for node in self.nodes:
            self.tree_map[node] = DomTreeNode(node, list())

        # Add all nodes except for the root node into the tree:
        for node in self.nodes:
            if self._idom[node]:
                parent = self.tree_map[self._idom[node]]
                node = self.tree_map[node]
                parent.children.append(node)
        self.root_tree = self.tree_map[self.entry_node]
        return self.root_tree

    def calculate_immediate_post_dominators(self):
        """ Calculate immediate post dominators for all nodes.

        Do this by choosing n from spdom(x) such that pdom(n) == spdom(x).
        """
        if self._pdom is None:
            self.calculate_post_dominators()

        if self._spdom is None:
            self.calculate_strict_dominators()

        self._ipdom = {}

        for node in self.nodes:
            if self._spdom[node]:
                for x in self._spdom[node]:
                    if self._pdom[x] == self._spdom[node]:
                        # This must be the only definition of ipdom:
                        assert node not in self._ipdom
                        self._ipdom[node] = x
            else:
                # No strict post dominators, hence also no
                # immediate post dominator:
                self._ipdom[node] = None

    def calculate_reach(self):
        """ Calculate which nodes can reach what other nodes """
        self.validate()

        # Initialize reach map:
        self._reach = {}
        for node in self.nodes:
            self._reach[node] = self.successors(node)

        # Run fixed point iteration:
        change = True
        while change:
            change = False
            for node in self.nodes:

                # Fill reachable condition:
                new_reach = set(self._reach[node])  # Take the old reach
                for m in node.successors:
                    new_reach |= self._reach[m]

                if new_reach != self._reach[node]:
                    change = True
                    self._reach[node] = new_reach

    def calculate_loops(self):
        """ Calculate loops by use of the dominator info """
        if self._reach is None:
            self.calculate_reach()

        loops = []
        for node in self.nodes:
            for header in self.successors(node):
                if header.dominates(node):
                    # Back edge!
                    # Determine the other nodes in the loop:
                    loop_nodes = [
                        ln for ln in self._reach[header]
                        if (header.dominates(ln)
                            and ln.can_reach(header) and ln is not header)]
                    loop = Loop(header=header, rest=loop_nodes)
                    loops.append(loop)
        return loops

    def calculate_dominance_frontier(self):
        """ Calculate the dominance frontier.

        Algorithm from Ron Cytron et al.

        how to calculate the dominance frontier for all nodes using
        the dominator tree.
        """
        if self.root_tree is None:
            self.calculate_dominator_tree()

        self.df = {}
        for x in self.bottom_up(self.root_tree):
            # Initialize dominance frontier to the empty set:
            self.df[x] = set()

            # Local rule for dominance frontier:
            for y in self.successors(x):
                if self.get_immediate_dominator(y) != x:
                    self.df[x].add(y)

            # upwards rule:
            for z in self.children(x):
                for y in self.df[z]:
                    if self.get_immediate_dominator(y) != x:
                        self.df[x].add(y)

    def bottom_up(self, tree):
        """ Generator that yields all nodes in bottom up way """
        for c in tree.children:
            for cc in self.bottom_up(c):
                yield cc
        yield tree.node

    def children(self, n):
        """ Return all children for node n """
        tree = self.tree_map[n]
        for c in tree.children:
            yield c.node


class ControlFlowNode(DiNode):
    def __init__(self, graph, name=None):
        super().__init__(graph)
        self.name = name

    def dominates(self, other):
        """ Test whether this node dominates the other node """
        return self.graph.dominates(self, other)

    def post_dominates(self, other):
        """ Test whether this node post-dominates the other node """
        return self.graph.post_dominates(self, other)

    def can_reach(self, other):
        """ Test if this node can reach the another node """
        return self.graph.can_reach(self, other)

    def reached(self):
        """ Test if this node is reached """
        return self.graph._reach[self]

    def __repr__(self):
        value = self.name if self.name else id(self)
        return 'CFG-node({})'.format(value)
