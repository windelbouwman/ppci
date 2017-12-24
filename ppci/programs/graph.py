"""
Functions related to inspecting Program objects/classes in a graph.
"""

import json

from .base import Program, SourceCodeProgram, IntermediateProgram
from .base import MachineProgram, get_program_classes


def get_targets(program):
    """ Get the program names that the given Program instance/subclass
    can be compiled to.
    """
    subclasses = get_program_classes()
    if isinstance(program, str):
        program = get_program_classes()[program.lower()]
    cls = program
    if not isinstance(cls, type):
        cls = type(program)
    if not issubclass(cls, Program):
        raise TypeError('get_targets() needs Program instance or class.')

    targets = set()
    for method_name in dir(cls):
        if method_name.startswith('to_') and \
                callable(getattr(cls, method_name)):
            prog_name = method_name[3:]
            if prog_name in subclasses:
                targets.add(prog_name)
    return targets


def get_program_graph():
    """ Produce a networkx graph where the nodes are language names and the
    (directed) edges represent compilers.
    """
    from ppci.utils import graph
    IGNORE = '', 'sourcecode', 'intermediate', 'machine'
    subclasses = get_program_classes()

    g = graph.DiGraph()
    for name in subclasses.keys():
        if name not in IGNORE:
            g.add_node(name)
    for name, programClass in subclasses.items():
        for target in get_targets(programClass):
            g.add_edge(name, target)
    return g


def mcp(program, target_name):
    """ Find the chain of representations to go from the given Program instance
    to the target language. Returns None if no path was found.

    This is essentially the Minimum Cost Path algorithm, and we can
    improve this to weight costs in various ways.
    """
    subclasses = get_program_classes()

    # Init front list of (cost, program1, program2, ...)
    front = [(1, program.language, tgt) for tgt in get_targets(program)]
    chains = []  # valid chains, sorted by length
    visited = set()
    visited.add(program.language)

    while True:

        # Are any chains finished?
        for i in reversed(range(len(front))):
            chain = front[i]
            if chain[-1] == target_name:
                chains.append(chain[1:])  # skip costs
                front.pop(i)

        # Are we finished?
        if not front:
            break

        # Expand front to target of each node in the front
        new_visited = set()

        for i in reversed(range(len(front))):
            chain = front.pop(i)
            program = subclasses[chain[-1]]
            for tgt in get_targets(program):  # For each target
                if tgt not in visited:
                    new_chain = (chain[0] + 1, ) + chain[1:] + (tgt, )
                    front.append(new_chain)
                    new_visited.add(tgt)
        visited.update(new_visited)
        if not new_visited:
            break

    return chains


def get_program_classes_by_group():
    """ Return programs classes in three groups (source code, ir, machine code),
    sorted by language name, and with base classes excluded.
    """
    program_classes = get_program_classes()
    programs1, programs2, programs3 = [], [], []

    for program in sorted(program_classes.values(), key=lambda p: p.language):
        if program in (
                Program, SourceCodeProgram, IntermediateProgram,
                MachineProgram):
            pass
        elif issubclass(program, SourceCodeProgram):
            programs1.append(program)
        elif issubclass(program, IntermediateProgram):
            programs2.append(program)
        elif issubclass(program, MachineProgram):
            programs3.append(program)

    return programs1, programs2, programs3


def get_program_classes_html():
    """ Generate html to show program classes in a graph.
    """
    program_classes = get_program_classes()
    programs1, programs2, programs3 = get_program_classes_by_group()

    html = ''

    # Create elements
    columns = []
    for column in range(3):
        progs = (programs1, programs2, programs3)[column]
        text = ''
        for program in progs:
            id = 'ppci-program-{}'.format(program.language)
            link = '#{}'.format(program.__name__)
            t = "<a id='{}' href='{}' onmouseover='ppci_show_targets(\"{}\");'"
            t += " onmouseout='ppci_hide_targets();'>{}</a>"
            text += t.format(id, link, program.language, program.language)
            text += '\n'
        columns.append('<td>{}</td>'.format(text))

    table_html = (
        "<table class='ppci-programs'>\n" +
        "<tr><th><a href='#SourceCodeProgram'>Source code</a></th>" +
        "<th><a href='#IntermediateProgram'>Intermediate</a></th>" +
        "<th><a href='#MachineProgram'>Machine code</a></th></tr>\n" +
        "<tr>{}</tr></tr>\n".format(''.join(columns)) +
        "</table>")

    # Generate "graph"
    # - the references are sorted by group so that arrows dont cross
    graphdict = {}
    for source_program in programs1 + programs2 + programs3:
        targets = get_targets(source_program)
        graphdict[source_program.language] = sorted_targets = []
        for target_program in programs1 + programs2 + programs3:
            if target_program.language in targets:
                sorted_targets.append(target_program.language)

    html = HTML.replace('TABLE', table_html).replace('STYLE', STYLE)
    html = html.replace('JS', JS).replace('GRAPHDICT', json.dumps(graphdict))

    return html

# Below is some html/css/js that is included in the rst


HTML = """
<script>
var ppci_graphdict = GRAPHDICT;
JS
</script>

<style>
STYLE
</style>

TABLE
"""


STYLE = """
table.ppci-programs {
    width: 100%;
    max-width: 50em;
}
table.ppci-programs th{
    text-align: center;
    font-weight: bold;
    text-decoration: none;
}
table.ppci-programs th > a {
    text-decoration: none;
}
table.ppci-programs td > a {
    display: block;
    border: 1px solid rgba(0, 0, 0, 0.5);
    background: #fff;
    border-radius: 0.2em;
    padding: 0.1em 0.5em;
    margin: 0.5em 1em;
    font-size: 120%;
    text-align: center;
    text-decoration: none;
    color: #004;
}
table.ppci-programs td > a:hover {
    border: 1px solid rgba(0, 0, 255, 0.5);
}

table.ppci-programs td > a > div.ppci-arrow {
    position: absolute;
    z-index: 20;
    border: 1.5px solid rgba(0, 0, 255, 0.4);
    margin: 0;
    padding: 0;
    text-align: right;
    vertical-align: center;
    height: 0;
    font-size: 10px; /* get consistent arrow heads */
    transform-origin: top left;
}
table.ppci-programs td > a > div.ppci-arrow > i {
    border: 1.5px solid rgba(0, 0, 255, 0.4);
    border-width: 0 3px 3px 0;
    display: inline-block;
    margin: 0;
    padding: 4px;
    transform: translate(1px, -5.5px) rotate(-45deg);
}
"""

JS = """
function ppci_hide_targets() {
    for (var i=0; i<ppci_arrows.length; i++) {ppci_arrows[i].remove(); }
    ppci_arrows = [];
}

function ppci_show_targets(name) {
    var p1, p2, d1, d2, r1, r2, dist;

    d1 = document.getElementById('ppci-program-' + name);
    r1 = d1.getBoundingClientRect();

    var targets = ppci_graphdict[name];
    for (var i=0; i<targets.length; i++) {
        d2 = document.getElementById('ppci-program-' + targets[i]);
        r2 = d2.getBoundingClientRect();

        var xx = get_rect_edge_positions(r1, r2);
        p1 = xx[0]; p2 = xx[1]; dist = xx[2];
        p1 = [p1[0] + window.scrollX, p1[1] + window.scrollY];
        p2 = [p2[0] + window.scrollX, p2[1] + window.scrollY];
        var angle = Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);

        var arrow = document.createElement('div');
        arrow.className = 'ppci-arrow';
        arrow.appendChild(document.createElement('i'));
        d1.appendChild(arrow);
        ppci_arrows.push(arrow);

        arrow.style.left = p1[0] + 'px';
        arrow.style.top = p1[1] + 'px';
        arrow.style.width = dist + 'px';
        arrow.style.transform = 'rotate(' + angle + 'rad)';
    }
}

function get_rect_edge_positions(r1, r2) {
    var i, p1, p2, dist, p, d;

    p1 = c1 = [0.5 * (r1.left + r1.right), 0.5 * (r1.top + r1.bottom)];
    p2 = c2 = [0.5 * (r2.left + r2.right), 0.5 * (r2.top + r2.bottom)];
    dist = Math.pow(p1[0] - p2[0], 2) + Math.pow(p1[1] - p2[1], 2);

    // first select closest point on rect 1
    var positions1 = [
        [c1[0], r1.top], [c1[0], r1.bottom],
        [r1.left, c1[1]], [r1.right, c1[1]]];
    for (var i=0; i<4; i++) {
        p = positions1[i];
        d = Math.pow(p[0] - p2[0], 2) + Math.pow(p[1] - p2[1], 2);
        if (d < dist) { p1 = p; dist = d; }
    }
    // then select closest point on rect 2
    var positions2 = [
        [c2[0], r2.top], [c2[0], r2.bottom],
        [r2.left, c2[1]], [r2.right, c2[1]]];
    for (var i=0; i<4; i++) {
        p = positions2[i];
        d = Math.pow(p1[0] - p[0], 2) + Math.pow(p1[1] - p[1], 2);
        if (d < dist) { p2 = p; dist = d; }
    }
    return [p1, p2, Math.sqrt(dist)];
}

var ppci_arrows = [];
"""
