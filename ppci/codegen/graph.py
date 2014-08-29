
class Graph:
    """
       Generic graph base class.
       Can dump to graphiz dot format for example!
    """
    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.adj_map = {}

    def add_node(self, n):
        self.nodes.add(n)
        if n not in self.adj_map:
            self.adj_map[n] = set()

    def del_node(self, n):
        self.nodes.remove(n)

    def mask_node(self, n):
        # For now, delete the node, but we can but it into a masked set?
        self.del_node(n)

    def unmask_node(self, n):
        self.add_node(n)

    def add_edge(self, n, m):
        """ Add an edge from n to m """
        self.edges.add((n, m))
        self.edges.add((m, n))
        self.adj_map[n].add(m)
        self.adj_map[m].add(n)

    def has_edge(self, n, m):
        return (n, m) in self.edges

    def delEdge(self, n, m):
        self.edges.remove((n, m))
        self.edges.remove((m, n))

    def adjecent(self, n):
        """ Return all nodes with edges to n """
        return self.adj_map[n] & self.nodes

    def to_dot(self, f):
        """ Generate graphviz dot representation """
        for n in self.nodes:
            print('  {} [label="{}" shape=box3d];'.format(id(n), n), file=f)
        for n, m in self.edges:
            print('  {} -> {};'.format(id(n), id(m)), file=f)


class Node:
    """
       Node in a graph.
    """
    def __init__(self, g):
        self.g = g
        self.addDegree = 0    # Hack to increase degree

    @property
    def Adjecent(self):
        return self.g.adjecent(self)

    @property
    def Degree(self):
        return len(self.Adjecent) + self.addDegree


class DiGraph(Graph):
    """ Directed graph. """
    def __init__(self):
        super().__init__()
        self.suc_map = {}
        self.pre_map = {}

    def add_edge(self, n, m):
        """ Add a directed edge from n to m """
        assert n in self.nodes
        assert m in self.nodes
        self.edges.add((n, m))
        self.suc_map[n].add(m)
        self.pre_map[m].add(n)
        self.adj_map[n].add(m)
        self.adj_map[m].add(n)

    def add_node(self, n):
        super().add_node(n)
        if n not in self.suc_map:
            self.suc_map[n] = set()
        if n not in self.pre_map:
            self.pre_map[n] = set()

    def successors(self, n):
        return self.suc_map[n] & self.nodes

    def predecessors(self, n):
        return self.pre_map[n] & self.nodes


class DiNode(Node):
    @property
    def Succ(self):
        return self.g.successors(self)

    @property
    def Pred(self):
        return self.g.predecessors(self)

    def __gt__(self, other):
        return self in other.Succ
