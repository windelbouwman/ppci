from .graph import DiGraph, DiNode


class FlowGraphNode(DiNode):
    """ A node in the flow graph """
    def __init__(self, g, ins):
        super().__init__(g)
        self.ins = ins
        self.uses = set(ins.src)
        self.defs = set(ins.dst)
        self.live_in = set()
        self.live_out = set()

    def __repr__(self):
        r = '{}'.format(self.ins)
        if self.uses:
            r += ' uses:' + ', '.join(str(u) for u in self.uses)
        if self.defs:
            r += ' defs:' + ', '.join(str(d) for d in self.defs)
        return r



class FlowGraph(DiGraph):
    def __init__(self, instrs):
        """ Create a flowgraph from a list of abstract instructions """
        super().__init__()
        self._map = {}
        # Add nodes:
        for ins in instrs:
            n = FlowGraphNode(self, ins)
            self._map[ins] = n
            self.add_node(n)

        # Make edges:
        prev = None
        for ins in instrs:
            n = self._map[ins]
            if prev:
                self.add_edge(prev, n)
            if ins.jumps:
                prev = None
                for j in ins.jumps:
                    to_n = self._map[j]
                    self.add_edge(n, to_n)
            else:
                prev = n
