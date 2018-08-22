"""
    To create a nice report of what happened during compilation, this file
    implements several reporting types.

    Reports can be written to plain text, or html.
"""

import abc
import cgitb
from contextlib import contextmanager
from datetime import datetime
import logging
import io
from .. import ir
from .. import __version__
from ..common import CompilerError
from ..irutils import Writer
from .graph2svg import Graph, LayeredLayout
from ..codegen.selectiongraph import SGValue
from ..binutils.outstream import TextOutputStream


class ReportGenerator(metaclass=abc.ABCMeta):
    """ Implement all these function to create a custom reporting generator """

    def header(self):
        pass

    def footer(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        self.header()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(exc_value, CompilerError):
            self.dump_compiler_error(exc_value)

        if exc_type:
            self.dump_exception((exc_type, exc_value, traceback))

        self.footer()

    @abc.abstractmethod
    def heading(self, level, title):
        raise NotImplementedError()

    @abc.abstractmethod
    def message(self, msg):
        raise NotImplementedError()

    @abc.abstractmethod
    def dump_raw_text(self, text):
        raise NotImplementedError()

    def dump_ir(self, ir_module):
        pass

    def dump_source(self, name, source_code):
        pass

    def dump_wasm(self, wasm_module):
        """ Report web assembly module """
        self.dump_source('Web assembly module', wasm_module.to_string())

    def dump_sgraph(self, sgraph):
        pass

    def dump_dag(self, dags):
        pass

    @abc.abstractmethod
    def dump_exception(self, einfo):
        """ List the given exception in report """
        raise NotImplementedError()

    @abc.abstractmethod
    def dump_trees(self, trees):
        raise NotImplementedError()

    def dump_frame(self, frame):
        pass

    def dump_cfg_nodes(self, frame):
        pass

    def dump_ig(self, ig):
        pass

    @abc.abstractmethod
    def dump_instructions(self, instructions, arch):
        """ Print instructions """
        raise NotImplementedError()

    def dump_compiler_error(self, compiler_error):
        self.heading(3, 'Error')
        f = io.StringIO()
        compiler_error.print(file=f)
        self.dump_raw_text(f.getvalue())


class DummyReportGenerator(ReportGenerator):
    """ Report generator which reports into the void """
    def heading(self, level, title):
        pass

    def message(self, msg):
        pass

    def dump_exception(self, einfo):
        pass

    def dump_raw_text(self, text):
        pass

    def dump_trees(self, trees):
        pass

    def dump_instructions(self, instructions, arch):
        pass


class TextWritingReporter(ReportGenerator):
    def __init__(self, dump_file):
        self.dump_file = dump_file

    def close(self):
        self.dump_file.close()

    def print(self, *args, end='\n'):
        """ Convenience helper for printing to dumpfile """
        print(*args, end=end, file=self.dump_file)

    def dump_instructions(self, instructions, arch):
        """ Print instructions """
        asm_printer = arch.asm_printer
        text_stream = TextOutputStream(
            asm_printer, f=self.dump_file,
            add_binary=True)
        text_stream.emit_all(instructions)


class TextReportGenerator(TextWritingReporter):
    def header(self):
        self.print('Report!')

    def dump_ir(self, ir_module):
        writer = Writer(file=self.dump_file)
        if isinstance(ir_module, ir.Module):
            self.print('==========================')
            writer.write(ir_module, verify=False)
            self.print('==========================')
        elif isinstance(ir_module, ir.SubRoutine):
            self.print('==========================')
            writer.write_function(ir_module)
            self.print('==========================')
        else:  # pragma: no cover
            raise NotImplementedError(str(ir_module))

    def heading(self, level, title):
        self.print()
        self.print(title)
        markers = {1: '=', 2: '-'}
        marker = markers[level] if level in markers else '~'
        self.print(marker * len(title))
        self.print()

    def message(self, msg):
        self.print(msg)

    def dump_raw_text(self, text):
        self.print(text)

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        self.print("Selection dag:")
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_exception(self, einfo):
        self.print(cgitb.text(einfo))

    def dump_trees(self, trees):
        self.print("Selection trees:")
        for tree in trees:
            self.print('  {}'.format(tree))

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


def selection_graph_to_graph(sgraph):
    graph = Graph()
    node_map = {}  # Mapping from SGNode to Node
    for node in sgraph.nodes:
        name = str(node).replace("'", "")
        node_map[node] = graph.create_node(name)

    for edge in sgraph.edges:
        from_node = node_map[edge.src]
        to_node = node_map[edge.dst]
        color_map = {
            SGValue.CONTROL: 'red',
            SGValue.DATA: 'black',
            SGValue.MEMORY: 'blue'
        }

        if not graph.has_edge(from_node, to_node):
            edge2 = graph.create_edge(from_node, to_node)
            edge2.label = edge.name
            edge2.color = color_map[edge.kind]
    return graph


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
        self.message(
            'Generated on {} by ppci version {}'.format(
                datetime.today().ctime(),
                __version__))

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
                f = io.StringIO()
                writer = Writer(f)
                writer.write(ir_module, verify=False)
                self.dump_raw_text(f.getvalue())
        elif isinstance(ir_module, ir.SubRoutine):
            title = 'Function {}'.format(ir_module.name)
            with collapseable(self, title):
                f = io.StringIO()
                writer = Writer(f)
                writer.write_function(ir_module)
                self.dump_raw_text(f.getvalue())
        else:  # pragma: no cover
            raise NotImplementedError()

    def dump_source(self, name, source_code):
        """ Report web assembly module """
        with collapseable(self, name):
            self.dump_raw_text(source_code)

    def dump_raw_text(self, text):
        """ Spitout text not to be formatted """
        self.print('<pre>')
        self.print(text)
        self.print('</pre>')

    def dump_instructions(self, instructions, arch):
        with collapseable(self, 'Instructions'):
            self.print('<pre>')
            super().dump_instructions(instructions, arch)
            self.print('</pre>')

    def render_graph(self, graph):
        LayeredLayout().generate(graph)
        graph.to_svg(self.dump_file)

    def dump_sgraph(self, sgraph):
        with collapseable(self, 'Selection graph'):
            self.print(
                '<div>'
                '<p>Selection graph.</p><ul>'
                '<li>red=control dependency</li>'
                '<li>blue=memory dependency</li>'
                '<li>black=data dependency</li>'
                '</ul>')
            graph = selection_graph_to_graph(sgraph)
            self.render_graph(graph)
            self.print('</div>')
            self.print('<p><b>To be implemented</b></p>')

    def dump_dag(self, dags):
        """ Write selection dag to dumpfile """
        for dag in dags:
            self.print('Dag:')
            for root in dag:
                self.print("- {}".format(root))

    def dump_exception(self, einfo):
        self.print(cgitb.html(einfo))

    def dump_trees(self, trees):
        with collapseable(self, 'Selection trees'):
            self.print('<hr>')
            self.print('<pre>')
            for tree in trees:
                self.print('  {}'.format(tree))
            self.print('</pre>')

    def dump_frame(self, frame):
        """ Dump frame to file for debug purposes """
        with collapseable(self, 'Frame'):
            used_regs = list(sorted(frame.used_regs, key=lambda r: r.name))
            self.print('<p><div class="codeblock">')
            self.print(frame)
            self.print('<p>stack size: {}</p>'.format(frame.stacksize))
            self.print('<p>Used: {}</p>'.format(used_regs))
            self.print('<table border="1">')
            self.print('<tr>')
            self.print('<th>#</th><th>instruction</th>')
            self.print('<th>use</th><th>def</th><th>clobber</th>')
            self.print('<th>jump</th><th>move</th>')
            self.print('<th>gen</th><th>kill</th>')
            self.print('<th>live_in</th><th>live_out</th>')
            for ur in used_regs:
                self.print('<th>{}</th>'.format(ur))
            self.print('</tr>')
            for idx, ins in enumerate(frame.instructions):
                self.print('<tr>')
                self.print('<td>{}</td>'.format(idx))
                self.print('<td>{}</td>'.format(ins))
                self.print('<td>{}</td>'.format(str2(ins.used_registers)))
                self.print('<td>{}</td>'.format(str2(ins.defined_registers)))
                self.print('<td>{}</td>'.format(str2(ins.clobbers)))
                self.print('<td>', end='')
                if ins.jumps:
                    self.print(str2(ins.jumps), end='')
                self.print('</td>')

                self.print('<td>', end='')
                if ins.ismove:
                    self.print('yes', end='')
                self.print('</td>')

                self.print('<td>', end='')
                if hasattr(ins, 'gen'):
                    self.print(str2(ins.gen), end='')
                self.print('</td>')

                self.print('<td>', end='')
                if hasattr(ins, 'kill'):
                    self.print(str2(ins.kill), end='')
                self.print('</td>')

                self.print('<td>', end='')
                if hasattr(ins, 'live_in'):
                    self.print(str2(ins.live_in), end='')
                self.print('</td>')

                self.print('<td>', end='')
                if hasattr(ins, 'live_out'):
                    self.print(str2(ins.live_out), end='')
                self.print('</td>')
                for ur in used_regs:
                    self.print('<td>')
                    for r2 in ins.live_out:
                        if r2.color == ur.color:
                            self.print(r2.name)
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
