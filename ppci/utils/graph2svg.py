""" Implementation of a graph to svg formatter. """
from statistics import median
from .collections import OrderedSet


class Node:
    def __init__(self):
        self.nid = id(self)
        self.label = ''
        self.color = None
        self.width = 0
        self.height = 0
        self.children = []
        self.parents = []

    def set_label(self, label):
        self.label = label
        return self


class DummyNode(Node):
    pass


class Edge:
    def __init__(self, src, dst):
        assert isinstance(src, Node)
        assert isinstance(dst, Node)
        self.src = src
        self.dst = dst
        self.label = ''
        self.color = 'blue'

    def set_label(self, label):
        self.label = label
        return self

    def set_color(self, color):
        self.color = color
        return self

    @property
    def path_length(self):
        """ return length of the path given a layering """
        assert self.src.layer < self.dst.layer
        return self.dst.layer - self.src.layer


class Graph:
    def __init__(self):
        self.nodes = OrderedSet()
        self.edges = OrderedSet()
        self.node_map = {}
        self.edge_map = {}

    def add_node(self, node):
        assert isinstance(node, Node)
        self.nodes.add(node)
        self.node_map[node.nid] = node

    def remove_node(self, node):
        assert isinstance(node, Node)
        self.nodes.remove(node)
        self.node_map.pop(node.nid)

    def create_node(self, label=''):
        node = Node()
        node.set_label(label)
        self.add_node(node)
        return node

    def add_edge(self, edge):
        assert isinstance(edge, Edge)
        self.edges.add(edge)
        self.edge_map[(edge.src, edge.dst)] = edge

    def remove_edge(self, edge):
        self.edges.remove(edge)
        self.edge_map.pop((edge.src, edge.dst))

    def delete_edge(self, edge):
        self.remove_edge(edge)
        edge.src.children.remove(edge.dst)
        edge.dst.parents.remove(edge.src)

    def create_edge(self, src, dst):
        edge = Edge(src, dst)
        assert not self.has_edge(src, dst)
        src.children.append(dst)
        dst.parents.append(src)
        self.add_edge(edge)
        return edge

    def has_edge(self, src, dst):
        """ Check if there is an edge from src to dst """
        return (src, dst) in self.edge_map

    def get_edge(self, src, dst):
        return self.edge_map[(src, dst)]

    def get_node(self, nid):
        return self.node_map[nid]

    def print(self, *args):
        """ Convenience helper for printing to dumpfile """
        print(*args, file=self.dump_file)

    def to_svg(self, f):
        self.dump_file = f
        spacex = 20

        # Render graph:
        width = self.width
        height = self.height
        self.print('<svg width="{}" height="{}">'.format(width, height))

        # Define an arrow marker:
        self.print(
            '<marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" '
            'markerUnits="strokeWidth" markerWidth="4" markerHeight="5" '
            'orient="auto">'
            '<path d="M 0 0 L 10 5 L 0 10 z"/>'
            '</marker>')
        self.print('<rect width="{}" height="{}"'.format(width, height))
        self.print(' x="0" y="0" style="fill:green;opacity:0.1" />')

        for node in self.nodes:
            x, y = node.x, node.y
            height = node.height
            width = node.width

            if isinstance(node, DummyNode):
                continue

            # Render box:
            self.print('<rect x="{}" y="{}" rx="3" ry="3"'.format(x, y))
            self.print(' width="{}" height="{}"'.format(width, height))
            self.print(' style="fill:red;opacity:0.1;stroke-width:1" />')
            # Render text:
            self.print('<text x="{0}" y="{1}" '.format(x + 3, y + height - 3))
            self.print('fill="black">{0}</text>'.format(node.label))

        for edge in self.edges:
            self.draw_path(edge)

        self.print('</svg>')

    def draw_path(self, edge):
        src, dst = edge.src, edge.dst
        x1, y1 = src.x + src.width // 2, src.y + src.height
        x2, y2 = dst.x + dst.width // 2, dst.y
        path = [Point(x1, y1)] + edge.path + [Point(x2, y2)]
        point_string = ' '.join('{},{}'.format(p.x, p.y) for p in path)
        self.print('<polyline points="{}"'.format(point_string))
        self.print(' stroke="{}" stroke-width="3"'.format(edge.color))
        self.print(' fill="none"')
        self.print(' marker-end="url(#arrow)" />')


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Path:
    """ A sequence of points """
    def __init__(self, points=()):
        self.points = list(points)
        if not all(isinstance(p, Point) for p in points):
            raise TypeError('All elements must be points in {}'.format(points))

    def __radd__(self, other):
        if isinstance(other, list):
            return Path(other + self.points)
        else:
            raise TypeError('Cannot radd {} to this Path object'.format(other))

    def __add__(self, other):
        if isinstance(other, Path):
            return Path(self.points + other.points)
        elif isinstance(other, list):
            return Path(self.points + other)
        else:
            raise TypeError('Cannot add {} to this Path object'.format(other))

    def __iter__(self):
        return iter(self.points)


class LayeredLayout:
    """ Layout the nodes according to Sugiyama / Layered graph drawing.

    There are the following phases:
    1. Cycle removal: reverse certain directed edges to make the graph
       acyclic.
    2. Layer assignment
    3. Crossing reduction
    """
    def __init__(self):
        pass

    def _assign_layers(self, graph):
        """ Put nodes into layers.

        Strategy:
        - Mark all nodes unprocessed
        - Start at layer
        - For each unprocessed node:
        -    if all descendants are processed:
        -        add to layer
        - Repeat until all nodes are ranked
        """
        unranked = OrderedSet(graph.nodes)
        is_ranked = lambda n: n not in unranked
        layers = []
        while unranked:
            layer = OrderedSet()
            for node in unranked:
                if all(is_ranked(c) for c in node.parents):
                    layer.add(node)
            layers.append(list(layer))
            unranked = unranked - layer

        # Finalize layering:
        layers = list(layers)

        # Assign layer to nodes:
        for i, layer in enumerate(layers):
            for node in layer:
                node.layer = i

        return layers

    def _insert_dummies(self, graph, layers):
        """ Insert dummy nodes such that all edge lengths are 1 """
        # Gather all current long edges:
        long_edges = [e for e in graph.edges if e.path_length > 1]

        # Split long edges into shorter ones:
        for long_edge in long_edges:
            graph.delete_edge(long_edge)
            dummies = []

            for i in range(long_edge.src.layer + 1, long_edge.dst.layer):
                dummy = DummyNode()
                dummies.append(dummy)
                graph.add_node(dummy)
                dummy.layer = i
                layers[dummy.layer].append(dummy)

            node_sequence = [long_edge.src] + dummies + [long_edge.dst]
            for src, dst in zip(node_sequence[:-1], node_sequence[1:]):
                edge = graph.create_edge(src, dst)
                edge.color = long_edge.color

    def _minimize_crossings(self, graph, layers):
        """ Minimize the amount of crossings in the graph """
        # def count_crossings(l1, l2):
        #    for n in l2:
        #        for 
        layer_pairs = list(zip(layers[:-1], layers[1:]))
        for _ in range(9):
            # Forwards (keep layer 1 fixed):
            for layer1, layer2 in layer_pairs:
                # Assign median values:
                for n in layer2:
                    if n.parents:
                        n.mean = median([layer1.index(i) for i in n.parents])
                    else:
                        n.mean = layer2.index(n)
                layer2.sort(key=lambda n: n.mean)

            # Reverse (keep layer 2 fixed):
            for layer1, layer2 in reversed(layer_pairs):
                # Assign median values:
                for n in layer1:
                    if n.children:
                        n.mean = median([layer2.index(i) for i in n.children])
                    else:
                        n.mean = layer1.index(n)
                layer1.sort(key=lambda n: n.mean)
            # TODO

    def _fold_dummies(self, graph):
        # Enter path coordinates into each edge:
        for edge in graph.edges:
            edge.path = []

        dummies = [n for n in graph.nodes if isinstance(n, DummyNode)]

        for dummy in dummies:
            # graph.remove_node(dummy)
            e1 = graph.get_edge(dummy.parents[0], dummy)
            e2 = graph.get_edge(dummy, dummy.children[0])
            point = Point(
                dummy.x + dummy.width // 2,
                dummy.y + dummy.height // 2)
            path = Path([point])
            edge = graph.create_edge(dummy.parents[0], dummy.children[0])
            edge.path = e1.path + path + e2.path
            edge.color = e1.color
            # join edge:
            graph.delete_edge(e1)
            graph.delete_edge(e2)

    def generate(self, graph):
        # Assign layers:
        layers = self._assign_layers(graph)

        self._insert_dummies(graph, layers)

        self._minimize_crossings(graph, layers)

        # Place nodes:
        for row, layer in enumerate(layers):
            for col, node in enumerate(layer):
                node.x = 10 + col * 200
                node.y = 10 + row * 60
                node.width = 180
                node.height = 20

        self._fold_dummies(graph)

        graph.width = max(node.x + node.width for node in graph.nodes) + 10
        graph.height = max(node.y + node.height for node in graph.nodes) + 10
