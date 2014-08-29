import logging
from .graph import Graph, Node


class InterferenceGraphNode(Node):
    def __init__(self, g, varname):
        super().__init__(g)
        self.temps = [varname]
        self.moves = set()
        self.color = None

    def __repr__(self):
        return '{}({})'.format(self.temps, self.color)

    def __gt__(self, other):
        return str(self.temps) > str(other.temps)


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
        # Calculate liveness in CFG:
        ###
        # Liveness:
        #  in[n] = use[n] UNION (out[n] - def[n])
        #  out[n] = for s in n.succ in union in[s]
        ###
        for n in flowgraph.nodes:
            n.live_in = set()
            n.live_out = set()

        # Sort flowgraph nodes backwards:
        cfg_nodes = list(flowgraph.nodes)
        cfg_nodes.sort(reverse=True)

        # Dataflow fixed point iteration:
        n_iterations = 0
        change = True
        while change:
            change = False
            for n in cfg_nodes:
                _in = n.live_in
                _out = n.live_out
                n.live_in = n.uses | (n.live_out - n.defs)
                if n.Succ:
                    n.live_out = set.union(*(s.live_in for s in n.Succ))
                else:
                    n.live_out = set()
                n.live_out = n.live_out | n.defs
                change = change or (_in != n.live_in) or (_out != n.live_out)
            n_iterations += 1

        self.logger.debug('Iterations: {} * {}'.format(n_iterations, len(cfg_nodes)))

        # Construct interference graph:
        for n in flowgraph.nodes:
            for tmp in n.live_out:
                n1 = self.get_node(tmp)
                for tmp2 in (n.live_out - {tmp}):
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
        if tmp in self.temp_map:
            n = self.temp_map[tmp]
            assert tmp in n.temps
        else:
            n = InterferenceGraphNode(self, tmp)
            self.add_node(n)
            self.temp_map[tmp] = n
        return n

    def combine(self, n, m):
        """ Combine n and m into n and return n """
        # Copy associated moves and temporaries into n:
        n.temps.extend(m.temps)
        n.moves.update(m.moves)

        # Update local temp map:
        for tmp in m.temps:
            self.temp_map[tmp] = n

        # Reroute all edges:
        e1 = [e for e in self.edges if e[0] is m]
        e2 = [e for e in self.edges if e[1] is m]
        for e in e1:
            self.edges.remove(e)
            self.add_edge(n, e[1])
        for e in e2:
            self.edges.remove(e)
            self.add_edge(n, e[0])

        # Remove node m:
        self.del_node(m)
        return n
