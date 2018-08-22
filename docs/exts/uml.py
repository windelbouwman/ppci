import tempfile
import subprocess
import os
from docutils.parsers.rst import Directive
from sphinx.ext.graphviz import graphviz

import pylint  # ensure that pyreverse is available

__version__ = '0.1'


def list_option(txt):
    return [p.strip() for p in txt.split(',')]


class UmlDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {
        'classes': list_option,
    }

    def run(self):
        module = self.arguments[0]

        # Generate dot:
        save_dir = os.getcwd()
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        basename = 'foo'
        cmd = ['pyreverse', '-p', basename]
        classes = self.options.get('classes', [])
        for c in classes:
            raise NotImplementedError('classes option')
            cmd.extend(['-c', c])
        cmd.append(module)
        subprocess.check_call(cmd)
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
