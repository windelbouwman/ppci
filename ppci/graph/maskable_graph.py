
from .graph import Graph


# TODO: take all masking behavior from Graph and put it here.
# Not all graph's require masking.


class MaskableGraph(Graph):
    """ A graph that allows masking nodes temporarily """
    def __init__(self):
        super().__init__()

    def del_node(self, n):
        """ Remove a node from the graph """
        assert n not in self.masked_nodes, 'Unable to delete masked node'
        super().del_node(n)

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
        super().combine(n, m)
