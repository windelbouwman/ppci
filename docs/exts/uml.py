import tempfile
import subprocess
import os
from sphinx.util.compat import Directive
from sphinx.ext.graphviz import graphviz

__version__ = '0.1'


class UmlDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def run(self):
        module = self.arguments[0]

        # Generate dot:
        save_dir = os.getcwd()
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        basename = 'foo'
        subprocess.call(['pyreverse', '-p', basename, module])
        with open('classes_{}.dot'.format(basename)) as f:
            dotcode = f.read()
        os.chdir(save_dir)

        # create graphviz node:
        node = graphviz()
        node['code'] = dotcode
        node['options'] = {}
        return [node]


def setup(app):
    app.add_directive('uml', UmlDirective)
    return {'version': __version__}
