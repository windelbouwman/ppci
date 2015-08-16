"""
    Implementation of a graph to svg formatter.
"""


class Node:
    def __init__(self, nid):
        self.nid = nid
        self.label = ''

    def set_label(self, label):
        self.label = label
        return self


class Edge:
    def __init__(self, src, dst):
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


class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = set()
        self.node_map = {}

    def add_node(self, nid, label=''):
        node = Node(nid)
        self.nodes.add(node)
        self.node_map[nid] = node
        node.set_label(label)
        return node

    def add_edge(self, src, dst):
        edge = Edge(src, dst)
        self.edges.add(edge)
        return edge

    def get_node(self, nid):
        return self.node_map[nid]

    def print(self, *args):
        """ Convenience helper for printing to dumpfile """
        print(*args, file=self.dump_file)

    def to_svg(self, f):
        self.dump_file = f

        # Render graph:
        width = self.width
        height = self.height
        self.print('<svg width="{}" height="{}">'.format(width, height))
        self.print('<rect width="{}" height="{}"'.format(width, height))
        self.print(' x="0" y="0" style="fill:green;opacity:0.1" />')
        for node in self.nodes:
            x, y = node.x, node.y
            height = node.height
            width = node.width
            # Render box:
            self.print('<rect x="{}" y="{}" rx="3" ry="3"'.format(x, y))
            self.print(' width="{}" height="{}"'.format(width, height))
            self.print(' style="fill:red;opacity:0.1;stroke-width:1" />')
            # Render text:
            self.print('<text x="{0}" y="{1}" '.format(x + 3, y + height - 3))
            self.print('fill="black">{0}</text>'.format(node.label))
        for edge in self.edges:
            src = self.get_node(edge.src)
            dst = self.get_node(edge.dst)
            x1, y1 = src.x, src.y
            x2, y2 = dst.x, dst.y
            self.print('<polyline points="{},{} {},{}"'.format(x1, y1, x2, y2))
            self.print(' style="stroke:black;stroke-width:1" />')
        self.print('</svg>')


class LayeredLayout:
    """
        Layout the nodes according to Sugiyama / Layered graph drawing
    """
    def __init__(self):
        pass

    def generate(self, graph):
        # Determine rank:

        # Place nodes:
        y = 10
        for node in graph.nodes:
            x = 10
            node.x = x
            node.y = y
            node.width = 200
            node.height = 20
            y = y + 25

        graph.width = max(node.x + node.width for node in graph.nodes) + 10
        graph.height = max(node.y + node.height for node in graph.nodes) + 10
