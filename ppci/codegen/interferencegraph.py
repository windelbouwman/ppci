import logging
from .graph import Graph, Node
from ..irmach import VirtualRegister


class InterferenceGraphNode(Node):
    __slots__ = ['temps', 'move']

    def __init__(self, g, varname):
        super().__init__(g)
        self.temps = {varname}
        self.moves = set()
        self.color = None

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

    def to_dot(self, f):
        """ Generate graphviz dot representation """
        for n in self.nodes:
            print('  {} [label="{}" shape=box3d];'.format(id(n), n), file=f)
        for n, m in self.edges:
            print('  {} -> {};'.format(id(n), id(m)), file=f)

    def to_txt(self):
        for node in self.nodes:
            print('{} interferes: {}'.format(node, node.Adjecent))

    def get_node(self, tmp):
        """ Get the node for a vreg """
        # Linear search
        assert type(tmp) is VirtualRegister
        if tmp in self.temp_map:
            n = self.temp_map[tmp]
            assert tmp in n.temps
        else:
            n = InterferenceGraphNode(self, tmp)
            self.add_node(n)
            self.temp_map[tmp] = n
        return n

    def interfere(self, tmp1, tmp2):
        """ Checks if tmp1 and tmp2 interfere """
        assert type(tmp1) is VirtualRegister
        assert type(tmp2) is VirtualRegister
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
