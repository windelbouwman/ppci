"""
    To create a nice report of what happened during compilation, this file
    implements several reporting types.

    Reports can be written to plain text, or html.
"""

from contextlib import contextmanager
import io
from .irutils import Writer
from .utils.graph2svg import Graph, LayeredLayout
from .codegen.selectiongraph import SGValue


class ReportGenerator:
    """ Implement all these function to create a custom reporting generator """
    def header(self):
        pass

    def footer(self):
        pass

    def heading(self, level, title):
        pass

    def message(self, msg):
        pass

    def dump_ir(self, ir_module):
        pass

    def dump_sgraph(self, sgraph):
        pass

    def dump_dag(self, dags):
        pass

    def dump_frame(self, frame):
        pass

    def dump_cfg_nodes(self, frame):
        pass

    def function_header(self, irfunc, target):
        pass

    def function_footer(self, instruction_list):
        pass


class DummyReportGenerator(ReportGenerator):
    def __init__(self):
        self.dump_file = io.StringIO()


class TextWritingReporter(ReportGenerator):
    def __init__(self, dump_file):
        self.dump_file = dump_file

    def print(self, *args):
        """ Convenience helper for printing to dumpfile """
        print(*args, file=self.dump_file)


@contextmanager
def complete_report(reporter):
    """
        Context wrapper that adds header and footer to the report

        Use it in a with statement like:
        with complete_report(generator) as reporter:
            reporter.message('Woot')
    """
    reporter.header()
    yield reporter
    reporter.footer()
    reporter.dump_file.close()


class TextReportGenerator(TextWritingReporter):
    def dump_ir(self):
        self.print('Before optimization {} {}'.format(ircode, ircode.stats()))
        writer = Writer()
        print('==========================', file=lst_file)
        writer.write(ircode, lst_file)
        print('==========================', file=lst_file)

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        self.print("Selection dag:")
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_frame(self, frame):
        """ Dump frame to file for debug purposes """
        self.print(frame)
        for ins in frame.instructions:
            self.print('$ {}'.format(ins))

    def dump_cfg_nodes(self, frame):
        for ins in frame.instructions:
            if frame.cfg.has_node(ins):
                nde = frame.cfg.get_node(ins)
                self.print('ins: {} {}'.format(ins, nde.longrepr))

    def header(self):
        pass

    def function_header(self, irfunc, target):
        self.print("========= Log for {} ==========".format(irfunc))
        self.print("Target: {}".format(target))
        # Writer().write_function(irfunc, f)

    def function_footer(self, instruction_list):
        for ins in instruction_list:
            self.print(ins)

        self.print("===============================")


@contextmanager
def collapseable(html_generator, title):
    guid = html_generator.new_guid()
    html_generator.print('<div class="well">')
    #html_generator.print('<span>{}'.format(title))
    #html_generator.print('<button type="button" class="btn btn-info" data-toggle="collapse" data-target="#{}">Show</button></span>'.format(guid))
    #html_generator.print('<div class="collapse" id="{}">'.format(guid))
    yield html_generator
    # html_generator.print('</div>')
    html_generator.print('</div>')


class HtmlReportGenerator(TextWritingReporter):
    def __init__(self, dump_file):
        super().__init__(dump_file)
        self.nr = 0

    def new_guid(self):
        self.nr += 1
        return 'guid_{}'.format(self.nr)

    def header(self):
        header = """<html><head>
  <!-- Latest compiled and minified CSS -->
  <link rel="stylesheet"
  href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">

  <!-- jQuery library -->
  <script
  src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js">
  </script>

  <!-- Latest compiled JavaScript -->
  <script 
  src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js">
  </script>

  <style>
  .body {
    margin: auto;
    width: 800px;
  }
  .graphdiv {
    width: 500px;
    height: 500px;
    border: 1px solid gray;
  }
  </style>
 </head>
 <body><div class="body container">
 <h1>Compilation report</h1>
 <p>
 This is an automatically generated report with a full log of compilation.
 </p>
        """
        self.print(header)

    def footer(self):
        footer = """
        </div>
        </body></html>
        """
        self.print(footer)

    def message(self, msg):
        self.print('<p>{}</p>'.format(msg))

    def dump_ir(self, ir_module):
        title = 'Module {}'.format(ir_module.name)
        with collapseable(self, title):
            self.print('<pre>')
            writer = Writer()
            f = io.StringIO()
            writer.write(ir_module, f)
            self.print(f.getvalue())
            self.print('</pre>')

    def function_header(self, irfunc, target):
        self.print("<h3> Log for {} </h3>".format(irfunc))
        self.print("<p>Target: {}</p>".format(target))
        # Writer().write_function(irfunc, f)

    def function_footer(self, instruction_list):
        with collapseable(self, 'Selected instructions'):
            self.print('<pre>')
            for ins in instruction_list:
                self.print(ins)
            self.print('</pre>')

    def render_graph(self, graph):
        LayeredLayout().generate(graph)
        graph.to_svg(self.dump_file)

    def render_graph2(self, graph):
        guid = self.new_guid()
        # self.print(sgraph.nodes)
        self.print('<div id="{}" class="graphdiv">'.format(guid))
        self.print('</div><script type="text/javascript">')
        self.print("var nodes = new vis.DataSet([")
        for node in graph.nodes:
            self.print("{{id: {}, label: '{}'}},".format(node.nid, node.label))
        self.print("]);")
        self.print("var edges = new vis.DataSet([")
        for edge in graph.edges:
            self.print("{{from: {}, to: {}, arrows: 'to', color: '{}' }},".format(edge.src, edge.dst, edge.color))
        self.print("]);")
        self.print("var container = document.getElementById('{}');".format(guid))
        self.print("var data = { nodes: nodes, edges: edges };")
        self.print("var options = {};")
        self.print("var network = new vis.Network(container, data, options);")
        self.print("</script>")

    def dump_sgraph(self, sgraph):
        graph = Graph()
        node_map = {}  # Mapping from SGNode to id of vis
        node_nr = 0
        for node in sgraph.nodes:
            node_nr += 1
            nid = node_nr
            node_map[node] = nid
            name = str(node).replace("'", "")
            graph.add_node(nid, name)
        for edge in sgraph.edges:
            from_nid = node_map[edge.src]
            to_nid = node_map[edge.dst]
            color_map = {
                SGValue.CONTROL: 'red',
                SGValue.DATA: 'black',
                SGValue.MEMORY: 'blue'
                }
            edge2 = graph.add_edge(from_nid, to_nid).set_label(edge.name)
            edge2.set_color(color_map[edge.kind])
        self.render_graph(graph)

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_frame(self, frame):
        """ Dump frame to file for debug purposes """
        with collapseable(self, 'Frame'):
            self.print('<p><div class="codeblock"><pre>')
            self.print(frame)
            for ins in frame.instructions:
                self.print('$ {}'.format(ins))
            self.print('</pre></div></p>')

    def dump_cfg_nodes(self, frame):
        for ins in frame.instructions:
            if frame.cfg.has_node(ins):
                nde = frame.cfg.get_node(ins)
                self.print('ins: {} {}'.format(ins, nde.longrepr))
