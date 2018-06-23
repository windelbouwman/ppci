""" Control flow graph algorithms.

Functions present:

- dominators
- post dominators
- reachability
- dominator tree
- dominance frontier

"""

import logging
# TODO: this is possibly the third edition of flow graph code.. Merge at will!
from .digraph import DiGraph, DiNode
from . import lt
from .algorithm.fixed_point_dominator import calculate_dominators
from .algorithm.fixed_point_dominator import calculate_post_dominators
from .algorithm.fixed_point_dominator import calculate_immediate_post_dominators
from collections import namedtuple

DomTreeNode = namedtuple('DomTreeNode', ['node', 'children'])
Loop = namedtuple('Loop', ['header', 'rest'])
logger = logging.getLogger('cfg')


def ir_function_to_graph(ir_function):
    """ Take an ir function and create a cfg of it """
    block_map = {}
    cfg = ControlFlowGraph()
    cfg.exit_node = ControlFlowNode(cfg, name=None)

    # Create nodes:
    block_list = []
    worklist = [ir_function.entry]
    while worklist:
        block = worklist.pop(0)
        block_list.append(block)
        node = ControlFlowNode(cfg, name=block.name)
        assert block not in block_map
        block_map[block] = node
        for successor_block in block.successors:
            if successor_block not in block_map:
                if successor_block not in worklist:
                    worklist.append(successor_block)

    cfg.entry_node = block_map[ir_function.entry]

    # Add edges:
    for block in block_list:
        # Fetch node:
        node = block_map[block]

        # Add proper edges:
        if len(block.successors) == 0:
            # Exit or return!
            node.add_edge(cfg.exit_node)
        else:
            for successor_block in block.successors:
                successor_node = block_map[successor_block]
                node.add_edge(successor_node)

            # TODO: hack to store yes and no blocks:
            if len(block.successors) == 2:
                node.yes = block_map[block.last_instruction.lab_yes]
                node.no = block_map[block.last_instruction.lab_no]

    logger.debug(
        'created cfg for %s with %s nodes', ir_function.name, len(cfg))
    return cfg, block_map


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

        # Dominator info:
        self._dom = None  # dominators
        self._sdom = None  # Strict dominators
        self._idom = None  # immediate_dominators

        # Post dominator info:
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
            self._calculate_dominator_info()
        return one in self._dom[other]

    def strictly_dominates(self, one, other):
        """ Test whether a node strictly dominates another node """
        if self._sdom is None:
            self._calculate_dominator_info()
        return one in self._sdom[other]

    def post_dominates(self, one, other):
        """ Test whether a node post dominates another node """
        if self._pdom is None:
            self._calculate_post_dominator_info()
        return one in self._pdom[other]

    def get_immediate_dominator(self, node):
        """ Retrieve a nodes immediate dominator """
        if self._idom is None:
            self._calculate_dominator_info()
        return self._idom[node]

    def get_immediate_post_dominator(self, node):
        """ Retrieve a nodes immediate post dominator """
        if self._ipdom is None:
            self._calculate_post_dominator_info()
        return self._ipdom[node]

    def can_reach(self, one, other):
        if self._reach is None:
            self.calculate_reach()
        return other in self._reach[one]

    def _calculate_dominator_info(self):
        """ Calculate dominator information """
        self.validate()

        # First calculate the dominator tree:
        self._idom = lt.calculate_idom(self, self.entry_node)
        self._calculate_dominator_tree()

        # Now calculate dominator sets:
        # Old method used the fixed point iteration:
        # self._dom = calculate_dominators(self.nodes, self.entry_node)
        self._dom = {}
        for parent, t in pre_order(self.root_tree):
            if parent:
                self._dom[t.node] = {t.node} | self._dom[parent.node]
            else:
                self._dom[t.node] = {t.node}

        self._sdom = {}
        for node in self.nodes:
            if node not in self._dom:
                self._dom[node] = {node}
                self._sdom[node] = set()
            else:
                self._sdom[node] = self._dom[node] - {node}

    def _calculate_dominator_tree(self):
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

    def _calculate_post_dominator_info(self):
        """ Calculate the post dominator sets iteratively.

        Post domination is the same as domination, but then starting at
        the exit node.
        """
        self.validate()

        self._pdom = calculate_post_dominators(self.nodes, self.exit_node)

        # Determine strict post dominators:
        self._spdom = {}
        for node in self.nodes:
            self._spdom[node] = self._pdom[node] - {node}

        self._ipdom = calculate_immediate_post_dominators(
            self.nodes, self._pdom, self._spdom)

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
            self._calculate_dominator_info()

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
        for t in bottom_up(tree):
            yield t.node

    def children(self, n):
        """ Return all children for node n """
        tree = self.tree_map[n]
        for c in tree.children:
            yield c.node


def bottom_up_recursive(tree):
    """ Generator that yields all nodes in bottom up way """
    for c in tree.children:
        for cc in bottom_up_recursive(c):
            yield cc
    yield tree


def bottom_up(tree):
    """ Generator that yields all nodes in bottom up way """
    worklist = [tree]
    visited = set()
    while worklist:
        node = worklist[-1]
        if id(node) in visited:
            worklist.pop()
            yield node
        else:
            visited.add(id(node))
            for child in node.children:
                worklist.append(child)


def pre_order(tree):
    """ Traverse tree in pre-order """
    worklist = [(None, tree)]
    while worklist:
        parent, node = worklist.pop(0)
        yield parent, node
        for child in node.children:
            worklist.append((node, child))


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
