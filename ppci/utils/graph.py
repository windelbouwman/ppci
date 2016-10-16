
from collections import defaultdict


def topological_sort(nodes):
    """ Sort nodes topological, use Tarjan algorithm here
        See: https://en.wikipedia.org/wiki/Topological_sorting
    """
    unmarked = set(nodes)
    marked = set()
    temp_marked = set()
    L = []

    def visit(n):
        # print(n)
        assert n not in temp_marked, 'DAG has cycles'
        if n in unmarked:
            temp_marked.add(n)
            for m in n.children:
                visit(m)
            temp_marked.remove(n)
            marked.add(n)
            unmarked.remove(n)
            L.insert(0, n)

    while unmarked:
        n = next(iter(unmarked))
        visit(n)

    return L


class Graph:
    """ Generic graph base class.

    Can dump to graphviz dot format for example!
    """

    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.masked_nodes = set()

        # Fast lookup dictionaries:
        self.adj_map = defaultdict(set)
        self.degree_map = defaultdict(int)

    def __iter__(self):
        for node in self.current_nodes:
            yield node

    def __len__(self):
        return len(self.current_nodes)

    @property
    def current_nodes(self):
        return self.nodes - self.masked_nodes

    def add_node(self, node):
        """ Add a node to the graph """
        self.nodes.add(node)
        for neighbour in self.adj_map[node]:
            self.degree_map[neighbour] += 1

    def del_node(self, n):
        """ Remove a node from the graph """
        assert n not in self.masked_nodes, 'Unable to delete masked node'
        self.nodes.remove(n)
        for neighbour in self.adj_map[n]:
            self.degree_map[neighbour] -= 1
            self.adj_map[neighbour].remove(n)

    def mask_node(self, node):
        """ Add the node into the masked set """
        self.masked_nodes.add(node)
        for neighbour in self.adj_map[node]:
            self.degree_map[neighbour] -= 1
            self.get_degree(neighbour)  # FOr check

    def unmask_node(self, node):
        """ Unmask a node (put it back into the graph """
        self.masked_nodes.remove(node)
        for neighbour in self.adj_map[node]:
            self.degree_map[neighbour] += 1
            self.get_degree(neighbour)  # FOr check

    def is_masked(self, node):
        return node in self.masked_nodes

    def add_edge(self, n, m):
        """ Add an edge between n and m """
        if n == m:
            return
        assert n in self.nodes
        assert m in self.nodes
        if (n, m) not in self.edges:
            self.edges.add((n, m))
            self.edges.add((m, n))
            self.adj_map[n].add(m)
            self.adj_map[m].add(n)
            if not self.is_masked(n):
                self.degree_map[m] += 1
            if not self.is_masked(m):
                self.degree_map[n] += 1

    def has_edge(self, n, m):
        return (n, m) in self.edges

    def get_degree(self, node):
        """ Get the degree of a certain node """
        # deg = len(self.adjecent(node))
        deg2 = self.degree_map[node]
        # TODO: use the degree_map here!
        # assert deg == deg2, '{} != {}'.format(deg, deg2)
        return deg2

    def del_edge(self, n, m):
        """ Delete edge between n and m """
        assert n != m
        assert n in self.nodes
        assert m in self.nodes
        if (n, m) in self.edges:
            self.edges.remove((n, m))
            self.edges.remove((m, n))
            self.adj_map[m].remove(n)
            self.adj_map[n].remove(m)
            if not self.is_masked(n):
                self.degree_map[m] -= 1
            if not self.is_masked(m):
                self.degree_map[n] -= 1

    def combine(self, n, m):
        """ Merge nodes n and m into node n """
        assert n != m
        # assert not self.has_edge(n, m)
        # if self.has_edge(n, m):
        #    self.degree_map[n] += 1

        # node m is going away, make sure to unmask it first:
        if self.is_masked(m):
            self.unmask_node(m)

        assert not self.is_masked(n), 'Combining only allowed for non-masked'
        # assert not self.has_edge(n, m)

        # Reroute all edges:
        m_adjecent = set(self.adj_map[m])
        for a in m_adjecent:
            self.del_edge(m, a)
            self.add_edge(n, a)

        # Remove node m:
        assert len(self.adj_map[m]) == 0  # Node should not have neighbours
        assert 0 == self.degree_map[m], '{} != 0'.format(self.degree_map[m])
        self.del_node(m)

    def adjecent(self, n):
        """ Return all unmasked nodes with edges to n """
        return self.adj_map[n] - self.masked_nodes

    def to_dot(self):
        """ Render current graph to dot format """
        pass


class Node:
    """
       Node in a graph.
    """
    def __init__(self, graph):
        self.graph = graph
        self.graph.add_node(self)

    @property
    def adjecent(self):
        """ Get adjecent nodes in the graph """
        return self.graph.adjecent(self)

    @property
    def degree(self):
        """ Get the degree of this node (the number of neighbours) """
        return self.graph.get_degree(self)


class DiGraph(Graph):
    """ Directed graph. """
    def __init__(self):
        super().__init__()
        self.suc_map = defaultdict(set)
        self.pre_map = defaultdict(set)

    def add_edge(self, n, m):
        """ Add a directed edge from n to m """
        assert n in self.nodes
        assert m in self.nodes
        if (n, m) not in self.edges:
            self.edges.add((n, m))
            self.suc_map[n].add(m)
            self.pre_map[m].add(n)
            self.adj_map[n].add(m)
            self.adj_map[m].add(n)
            self.degree_map[m] += 1
            self.degree_map[n] += 1

    def successors(self, n):
        return self.suc_map[n] & self.nodes

    def predecessors(self, n):
        return self.pre_map[n] & self.nodes


class DiNode(Node):
    @property
    def Succ(self):
        return self.graph.successors(self)

    @property
    def Pred(self):
        return self.graph.predecessors(self)
