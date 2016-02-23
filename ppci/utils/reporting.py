"""
    To create a nice report of what happened during compilation, this file
    implements several reporting types.

    Reports can be written to plain text, or html.
"""

from contextlib import contextmanager
from datetime import datetime
import io
from .. import ir
from ..irutils import Writer
from .graph2svg import Graph, LayeredLayout
from ..codegen.selectiongraph import SGValue


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

    def dump_trees(self, ir_function, function_info):
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
    html_generator.print('<div><div class="code button">')
    yield html_generator
    html_generator.print('</div></div>')


HTML_HEADER = """<!DOCTYPE HTML>
<html><head>
  <style>
  .graphdiv {
    width: 500px;
    height: 500px;
    border: 1px solid gray;
  }
  .code {
   padding: 10px;
   border: 1px solid black;
   border-radius: 15px;
   margin: 10px;
   font-weight: bold;
   display: inline-block;
  }
  .button {
    border-left: 3px solid white;
    border-top: 3px solid white;
    border-right: 3px solid gray;
    border-bottom: 3px solid gray;
    background: lightgray;
  }
  body {
    font-family: sans-serif;
    background: floralwhite;
  }
  table {
    border-collapse: collapse;
  }

  table, th, rd {
    border: 1px solid black;
  }

  th, td {
    padding: 5px;
  }

  th {
    background: gray;
    color: white;
  }

  </style>
 </head>
 <body><div>
 <h1>Compilation report</h1>
 <p>This is an automatically generated report with a full log of compilation.
 </p>

"""

HTML_FOOTER = """
</div>
</body></html>
"""


class HtmlReportGenerator(TextWritingReporter):
    def __init__(self, dump_file):
        super().__init__(dump_file)
        self.nr = 0

    def new_guid(self):
        self.nr += 1
        return 'guid_{}'.format(self.nr)

    def header(self):
        self.print(HTML_HEADER)
        self.message(datetime.today().ctime())

    def footer(self):
        self.print(HTML_FOOTER)

    def message(self, msg):
        self.print('<p>{}</p>'.format(msg))

    def dump_ir(self, ir_module):
        if isinstance(ir_module, ir.Module):
            title = 'Module {}'.format(ir_module.name)
            with collapseable(self, title):
                self.print('<pre>')
                writer = Writer()
                f = io.StringIO()
                writer.write(ir_module, f)
                self.print(f.getvalue())
                self.print('</pre>')
        elif isinstance(ir_module, ir.Function):
            title = 'Function {}'.format(ir_module.name)
            with collapseable(self, title):
                self.print('<pre>')
                writer = Writer()
                writer.f = f = io.StringIO()
                writer.write_function(ir_module)
                self.print(f.getvalue())
                self.print('</pre>')
        else:
            raise NotImplementedError()

    def function_header(self, irfunc, target):
        self.print("<h3>Log for {}</h3>".format(irfunc))
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
        # self.render_graph(graph)
        self.print('<p><b>To be implemented</b></p>')

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_trees(self, ir_function, function_info):
        self.message('Selection trees for {}'.format(ir_function))
        with collapseable(self, 'trees'):
            self.print('<pre>')
            for ir_block in ir_function:
                self.print(str(ir_block))
                for tree in function_info.block_trees[ir_block]:
                    self.print('  {}'.format(tree))
            self.print('</pre>')

    def dump_frame(self, frame):
        """ Dump frame to file for debug purposes """
        with collapseable(self, 'Frame'):
            self.print('<p><div class="codeblock">')
            self.print(frame)
            self.print('<table border="1">')
            self.print('<tr><th>ins</th><th>use</th><th>def</th><th>jump</th></tr>')
            for ins in frame.instructions:
                self.print('<tr>')
                self.print('<td>$ {}</td>'.format(ins))
                self.print('<td>{}</td>'.format(ins.used_registers))
                self.print('<td>{}</td>'.format(ins.defined_registers))
                self.print('<td>')
                if ins.jumps:
                    self.print('{}'.format(ins.jumps))
                if ins.ismove:
                    self.print('MOVE')
                self.print('</td>')
                self.print('</tr>')
            self.print("</table>")
            self.print('</div></p>')

    def dump_cfg_nodes(self, frame):
        for ins in frame.instructions:
            if frame.cfg.has_node(ins):
                nde = frame.cfg.get_node(ins)
                self.print('ins: {} {}'.format(ins, nde.longrepr))
