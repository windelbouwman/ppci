import logging
from collections import defaultdict
from ..utils.graph import DiGraph, DiNode


class FlowGraphNode(DiNode):
    """ A node in the flow graph. A node can contain more than one
        instruction. """
    def __init__(self, g, ins):
        super().__init__(g)
        self.gen = set()
        self.kill = set()
        self.live_in = set()
        self.live_out = set()
        self.instructions = []

        # Start with the instruction itself..
        self.add_instruction(ins)

    def add_instruction(self, ins):
        """ Bundle the instruction into the current node. """
        ins.gen = set(ins.used_registers)
        ins.kill = set(ins.defined_registers)
        self.instructions.append(ins)

        # Combine gen and kill effects of the node and the new instruction:
        self.gen = self.gen | (ins.gen - self.kill)
        self.kill = self.kill | ins.kill

    def __repr__(self):
        r = 'CFG-node({})'.format(len(self.instructions))
        return r

    @property
    def longrepr(self):
        r = str(self)
        if self.gen:
            r += ' gen:' + ', '.join(str(u) for u in self.gen)
        if self.kill:
            r += ' kill:' + ', '.join(str(d) for d in self.kill)
        r += ' live_out={}, live_in={}'.format(self.live_out, self.live_in)
        r += ', Succ={}, Pred={}'.format(self.Succ, self.Pred)
        return r


class FlowGraph(DiGraph):
    """ A directed graph containing nodes with linear lists of instructions """
    def __init__(self, instrs):
        """ Create a flowgraph from a linear list of abstract instructions """
        super().__init__()
        self.logger = logging.getLogger('flowgraph')
        self._map = {}
        self._live_ranges = defaultdict(list)

        # TODO: make this very tricky part of code better readable!!!

        # Create leaders:
        node = None
        for ins in instrs:
            if node is None:
                # Get the first node:
                node = self.get_node(ins)
            if ins.jumps:
                # Do not create edges yet, as this would not
                # result in correct flow graph:
                for j in ins.jumps:
                    self.get_node(j)
                node = None

        # Add between nodes and follow up nodes:
        node = None
        for ins in instrs:
            if self.has_node(ins):
                node = self.get_node(ins)
            if ins.jumps:
                for j in ins.jumps:
                    to_node = self.get_node(j)
                    self.add_edge(node, to_node)

        # Add other instruction into leader nodes:
        node = None
        for ins in instrs:
            if self.has_node(ins):
                # Node is a leader:
                node = self.get_node(ins)
            else:
                # Node is not a leader, make sure we passed a leader already:
                assert node is not None
                node.add_instruction(ins)

    def has_node(self, ins):
        """ Return true if statement is a leader instruction """
        return ins in self._map

    def get_node(self, ins):
        """ Get the node belonging to the instruction """
        if ins not in self._map:
            node = FlowGraphNode(self, ins)
            self._map[ins] = node
            self.add_node(node)
        return self._map[ins]

    # def live_range(
    def calculate_liveness(self):
        """ Calculate liveness in CFG: """
        ###
        # Liveness:
        #  in[n] = use[n] UNION (out[n] - def[n])
        #  out[n] = for s in n.succ in union in[s]
        ###
        for node in self:
            node.live_in = set()
            node.live_out = set()

        # Sort flowgraph nodes backwards:
        cfg_nodes = list(self.nodes)

        # Dataflow fixed point iteration over the nodes in the CFG:
        n_iterations = 0
        change = True
        while change:
            change = False
            for node in cfg_nodes:
                _in = node.live_in
                _out = node.live_out
                node.live_in = node.gen | (node.live_out - node.kill)
                if node.Succ:
                    node.live_out = set.union(*(s.live_in for s in node.Succ))
                else:
                    node.live_out = set()

                # Record for change:
                change = change or (_in != node.live_in) or \
                    (_out != node.live_out)
            n_iterations += 1

        # In one pass fix all instructions:
        for node in self:
            assert len(node.instructions) > 0
            ins2 = node.instructions[-1]
            ins2.live_out = node.live_out  # Propagate into last instruction
            ins2.live_in = ins2.gen | (ins2.live_out - ins2.kill)
            if len(node.instructions) > 1:
                for ins in reversed(node.instructions[:-1]):
                    ins1 = ins

                    ins1.live_out = ins2.live_in
                    ins1.live_in = ins1.gen | (ins1.live_out - ins1.kill)

                    for vreg in (ins2.live_in & ins1.live_out):
                        self._live_ranges[vreg].append((ins1, ins2))

                    ins2 = ins1

        self.logger.debug(
            'Iterations: %s,  nodes: %s', n_iterations, len(self))
