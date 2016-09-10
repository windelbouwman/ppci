"""

.. autoclass:: ppci.codegen.interferencegraph.InterferenceGraph
    :members: get_node, combine, interfere

"""

import logging
from collections import defaultdict
from ..utils.graph import Graph, Node
from ..arch.registers import Register


class InterferenceGraphNode(Node):
    """ Node in an interference graph. Represents a single register """
    def __init__(self, graph, vreg):
        super().__init__(graph)
        self.temps = {vreg}
        self.moves = set()
        self.reg = vreg if vreg.is_colored else None
        self.reg_class = type(vreg)

    @property
    def is_colored(self):
        return self.reg is not None

    def __repr__(self):
        return '{}(reg={},class={})'.format(
            self.temps, self.reg, self.reg_class)


class InterferenceGraph(Graph):
    """ Interference graph. """
    def __init__(self):
        """ Create a new interference graph from a flowgraph """
        super().__init__()
        self.logger = logging.getLogger('interferencegraph')
        self.temp_map = {}
        self._def_map = defaultdict(list)
        self._use_map = defaultdict(list)

    def defs(self, tmp):
        return self._def_map[tmp]

    def uses(self, tmp):
        return self._use_map[tmp]

    def calculate_interference(self, flowgraph):
        """ Construct interference graph """
        for n in flowgraph:
            for ins in n.instructions:
                # ins.live_out |= ins.
                for tmp in ins.live_in:
                    self.get_node(tmp)

                # Live out and zero length defined variables:
                live_and_def = ins.live_out | ins.kill

                # Add interfering edges:
                for tmp in live_and_def:
                    n1 = self.get_node(tmp)
                    for tmp2 in (live_and_def - {tmp}):
                        n2 = self.get_node(tmp2)
                        self.add_edge(n1, n2)

                # Generate usage info:
                for reg in ins.defined_registers:
                    self._def_map[reg].append(ins)
                for reg in ins.used_registers:
                    self._use_map[reg].append(ins)

    def has_node(self, tmp):
        """ Check if there exists a node for this temp register """
        assert isinstance(tmp, Register)
        return tmp in self.temp_map

    def get_node(self, tmp, create=True):
        """ Get the node for a register """
        assert isinstance(tmp, Register)
        if tmp in self.temp_map:
            node = self.temp_map[tmp]
            assert tmp in node.temps
        else:
            assert create
            node = InterferenceGraphNode(self, tmp)
            self.add_node(node)
            self.temp_map[tmp] = node
        return node

    def interfere(self, tmp1, tmp2):
        """ Checks if tmp1 and tmp2 interfere """
        assert isinstance(tmp1, Register)
        assert isinstance(tmp2, Register)
        node1 = self.get_node(tmp1)
        node2 = self.get_node(tmp2)
        return self.has_edge(node1, node2)

    def combine(self, n, m):
        """ Combine n and m into n and return n """
        # Copy associated moves and temporaries into n:
        n.temps |= m.temps
        n.moves.update(m.moves)

        # Update local temp map:
        for tmp in m.temps:
            self.temp_map[tmp] = n

        super().combine(n, m)
        return n
