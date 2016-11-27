"""
    To create a nice report of what happened during compilation, this file
    implements several reporting types.

    Reports can be written to plain text, or html.
"""

from contextlib import contextmanager
from datetime import datetime
import logging
import io
from .. import ir
from ..irutils import Writer
from .graph2svg import Graph, LayeredLayout
from ..codegen.selectiongraph import SGValue
from ..arch.arch import Label


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

    def dump_ig(self, ig):
        pass

    def dump_instructions(self, instruction_list):
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
    def dump_ir(self, ir_module):
        self.print('Before optimization {} {}'.format(
            ir_module, ir_module.stats()))
        writer = Writer()
        self.print('==========================')
        writer.write(ir_module, self.dump_file)
        self.print('==========================')

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
    html_generator.print('<div><div class="button">')
    html_generator.print('<input type="checkbox" class="expand" />')
    html_generator.print('<h4>{}</h4>'.format(title))
    html_generator.print('<div>')
    html_generator.print('<hr>')
    yield html_generator
    html_generator.print('</div>')
    html_generator.print('</div></div>')


HTML_HEADER = """<!DOCTYPE HTML>
<html><head>
  <style>
  .expand {
    float: right;
  }
  .expand ~ div {
    overflow: hidden;
    height: auto;
    transition: height 2s ease;
  }
  h4 {
    margin: 0px;
  }
  .expand:not(:checked) ~ div {
    height: 0px;
  }
  .graphdiv {
    width: 500px;
    height: 500px;
    border: 1px solid gray;
  }
  .code {
   padding: 2px;
   border: 1px solid black;
   border-radius: 5px;
   margin: 2px;
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
    font-size: 8pt;
    border-collapse: collapse;
  }

  table, th, rd {
    border: 1px solid black;
  }

  th, td {
    padding: 1px;
  }

  th {
    background: gray;
    color: white;
  }

  tr:nth-child(2n) {
    background: lightblue;
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


def str2(x):
    return ', '.join(sorted(str(y) for y in x))


class MyHandler(logging.Handler):
    def __init__(self, backlog):
        super().__init__()
        self.backlog = backlog

    def emit(self, record):
        self.backlog.append(self.format(record))
        print(self, self.backlog[-1])


class HtmlReportGenerator(TextWritingReporter):
    def __init__(self, dump_file):
        super().__init__(dump_file)
        self.nr = 0
        self.backlog = []
        # This handler works nice, but when used multiple times, loggers
        # start to accumulate and accumulate, leading to memory error
        # logging.getLogger().addHandler(MyHandler(self.backlog))

    def new_guid(self):
        self.nr += 1
        return 'guid_{}'.format(self.nr)

    def flush_log(self):
        if self.backlog:
            with collapseable(self, 'Log'):
                self.print('<pre>')
                while self.backlog:
                    self.print(self.backlog.pop(0))
                self.print('<pre>')

    def header(self):
        self.print(HTML_HEADER)
        self.message(datetime.today().ctime())

    def footer(self):
        self.flush_log()
        self.print(HTML_FOOTER)

    def heading(self, level, title):
        self.flush_log()
        html_tags = {
            1: 'h1', 2: 'h2', 3: 'h3'
        }
        html_tag = html_tags[level]
        self.print('<{0}>{1}</{0}>'.format(html_tag, title))

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
        elif isinstance(ir_module, ir.SubRoutine):
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

    def dump_instructions(self, instruction_list):
        with collapseable(self, 'Instructions'):
            self.print('<pre>')
            for ins in instruction_list:
                if isinstance(ins, Label):
                    self.print('{}'.format(ins))
                else:
                    self.print('    {}'.format(ins))
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
        with collapseable(self, 'Selection graph'):
            self.print('<p><b>To be implemented</b></p>')

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_trees(self, ir_function, function_info):
        with collapseable(self, 'Selection trees'):
            self.message('Selection trees for {}'.format(ir_function))
            self.print('<hr>')
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
            self.print('<p>Used: {}</p>'.format(frame.used_regs))
            self.print('<table border="1">')
            self.print('<tr>')
            self.print('<th>#</th><th>instruction</th>')
            self.print('<th>use</th><th>def</th>')
            self.print('<th>jump</th><th>move</th>')
            self.print('<th>gen</th><th>kill</th>')
            self.print('<th>live_in</th><th>live_out</th>')
            self.print('</tr>')
            for idx, ins in enumerate(frame.instructions):
                self.print('<tr>')
                self.print('<td>{}</td>'.format(idx))
                self.print('<td>{}</td>'.format(ins))
                self.print('<td>{}</td>'.format(str2(ins.used_registers)))
                self.print('<td>{}</td>'.format(str2(ins.defined_registers)))
                self.print('<td>')
                if ins.jumps:
                    self.print(str2(ins.jumps))
                self.print('</td>')

                self.print('<td>')
                if ins.ismove:
                    self.print('yes')
                self.print('</td>')

                self.print('<td>')
                if hasattr(ins, 'gen'):
                    self.print(str2(ins.gen))
                self.print('</td>')

                self.print('<td>')
                if hasattr(ins, 'kill'):
                    self.print(str2(ins.kill))
                self.print('</td>')

                self.print('<td>')
                if hasattr(ins, 'live_in'):
                    self.print(str2(ins.live_in))
                self.print('</td>')

                self.print('<td>')
                if hasattr(ins, 'live_out'):
                    self.print(str2(ins.live_out))
                self.print('</td>')
                self.print('</tr>')
            self.print("</table>")
            self.print('</div></p>')

    def dump_cfg_nodes(self, frame):
        for ins in frame.instructions:
            if frame.cfg.has_node(ins):
                nde = frame.cfg.get_node(ins)
                self.print('ins: {} {}'.format(ins, nde.longrepr))

    def dump_ig(self, ig):
        ig.to_dot()
