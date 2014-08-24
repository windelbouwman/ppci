
import logging
import io

from .binutils import outstream
from .c3 import AstPrinter
from . import logformat
from .irutils import Writer

class RstFormatter(logging.Formatter):
    """ Formatter that tries to create an rst document """
    def __init__(self):
        super().__init__(fmt=logformat)

    # def print(self, *args):
    #   print(*args, file=x)
    def format(self, record):
        s = super().format(record)
        s += '\n'
        if hasattr(record, 'c3_ast'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            AstPrinter().printAst(record.c3_ast, f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'ircode'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            Writer('  ').write(record.ircode, f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'irfunc'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            Writer('  ').write_function(record.irfunc, f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'ppci_frame'):
            f = io.StringIO()
            frame = record.ppci_frame
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            print('  {}'.format(frame.name), file=f)
            for i in frame.instructions:
                print('   {}'.format(i), file=f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'dag'):
            f = io.StringIO()
            dags = record.dag
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            for dag in dags:
                for i in dag:
                    print('   {}'.format(i), file=f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'ra_cfg'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. graphviz::', file=f)
            print('', file=f)
            print('  digraph G {', file=f)
            print('    size="8,80";', file=f)
            cfg = record.ra_cfg
            cfg.to_dot(f)
            print('  }', file=f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'ra_ig'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. graphviz::', file=f)
            print('', file=f)
            print('  digraph G {', file=f)
            print('    ratio="compress";', file=f)
            print('    size="8,80";', file=f)
            ig = record.ra_ig
            ig.to_dot(f)
            print('  }', file=f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'ins_list'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            for ins in record.ins_list:
                print('   {}'.format(ins), file=f)
            print('', file=f)
            s += '\n' + f.getvalue()
        if hasattr(record, 'zcc_outs'):
            f = io.StringIO()
            print('', file=f)
            print('', file=f)
            print('.. code::', file=f)
            print('', file=f)
            outstream.OutputStreamWriter('  ').dump(record.zcc_outs, f)
            print('', file=f)
            s += '\n' + f.getvalue()
        return s


def generate_sphinx_docs():
    """ Generate report and convert it to pdf directly """
    from sphinx import quickstart
    d = dict(
        path = 'build',
        sep  = False,
        dot  = '_',
        project = opts.header,
        author = 'Author',
        version = '0',
        release = '0',
        suffix = '.rst',
        master = 'index',
        epub = False,
        ext_autodoc = True,
        ext_viewcode = True,
        makefile = True,
        batchfile = True,
        mastertocmaxdepth = 1,
        mastertoctree = text,
    )
    quickstart.generate(d)

