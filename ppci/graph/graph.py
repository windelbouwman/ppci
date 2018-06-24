""" Graph package.

"""

import abc
from collections import defaultdict
from ..utils.collections import OrderedSet


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


class BaseGraph(abc.ABC):
    """ Base graph class """
    def __init__(self):
        self.nodes = OrderedSet()

        # Fast lookup dictionaries:
        self.adj_map = defaultdict(OrderedSet)

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __len__(self):
        return len(self.nodes)

    def add_node(self, node):
        """ Add a node to the graph """
        self.nodes.add(node)

    @abc.abstractmethod
    def del_node(self, node):  # pragma: no cover
        """ Remove a node from the graph """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_edge(self, n, m):  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def del_edge(self, n, m):  # pragma: no cover
        raise NotImplementedError()

    def get_degree(self, node):
        """ Get the degree of a certain node """
        return len(self.adj_map[node])

    def adjecent(self, n):
        """ Return all unmasked nodes with edges to n """
        return self.adj_map[n]


class Graph(BaseGraph):
    """ Generic graph base class.

    Can dump to graphviz dot format for example!
    """
    def del_node(self, node):
        """ Remove a node from the graph """
        # Delete edges:
        for neighbour in list(self.adj_map[node]):
            self.del_edge(node, neighbour)
        self.nodes.remove(node)

    def add_edge(self, n, m):
        """ Add an edge between n and m """
        if n == m:
            return
        assert n in self.nodes
        assert m in self.nodes
        if not self.has_edge(n, m):
            self.adj_map[n].add(m)
            self.adj_map[m].add(n)

    def del_edge(self, n, m):
        """ Delete edge between n and m """
        assert n != m
        assert n in self.nodes
        assert m in self.nodes
        if self.has_edge(n, m):
            self.adj_map[m].remove(n)
            self.adj_map[n].remove(m)

    def has_edge(self, n, m):
        """ Test if there exist and edge between n and m """
        assert n in self.nodes
        assert m in self.nodes
        return m in self.adj_map[n]

    def combine(self, n, m):
        """ Merge nodes n and m into node n """
        assert n != m
        # assert not self.has_edge(n, m)
        # if self.has_edge(n, m):
        #    self.degree_map[n] += 1

        # assert not self.has_edge(n, m)

        # Reroute all edges:
        m_adjecent = set(self.adj_map[m])
        for a in m_adjecent:
            self.del_edge(m, a)
            self.add_edge(n, a)

        # Remove node m:
        assert len(self.adj_map[m]) == 0  # Node should not have neighbours
        self.del_node(m)

    def to_dot(self):
        """ Render current graph to dot format """
        pass


class Node:
    """ Node in a graph. """
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

    def add_edge(self, other):
        """ Create an edge to the other node """
        self.graph.add_edge(self, other)
