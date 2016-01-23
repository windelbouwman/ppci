
import logging
from ..utils.graph import Graph, Node
from ..arch.isa import Register


class InterferenceGraphNode(Node):

    def __init__(self, g, varname):
        super().__init__(g)
        self.temps = {varname}
        self.moves = set()
        self.color = varname.color

    def __repr__(self):
        return '{}({})'.format(self.temps, self.color)


class InterferenceGraph(Graph):
    """
        Interference graph.
    """
    def __init__(self, flowgraph):
        """ Create a new interference graph from a flowgraph """
        super().__init__()
        self.logger = logging.getLogger('interferencegraph')
        self.temp_map = {}
        self.calculate_interference(flowgraph)

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

    def get_node(self, tmp):
        """ Get the node for a register """
        assert isinstance(tmp, Register)
        if tmp in self.temp_map:
            node = self.temp_map[tmp]
            assert tmp in node.temps
        else:
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
