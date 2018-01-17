"""
Generate docs for program clases.
"""

import os
import json

from ppci import programs

__version__ = '0.1'

DOC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


files_to_remove = []


def setup(app):
    app.connect('build-finished', clean)
    write_programs_rst()


def clean(app, *args):
    for fname in files_to_remove:
        filename = os.path.join(DOC_DIR, fname)
        if os.path.isfile(filename):
            os.remove(filename)


def write_programs_rst():
    """ Genereate the RST.
    """
    
    parts = []
    
    # Create title
    parts.append('Program classes')
    parts.append('=' * len(parts[-1]))
    parts.append(' ')
    
    # Intro
    parts.append('.. automodule:: ppci.programs')
    parts.append('')
    
    # Add TOC
    toc_html = programs.get_program_classes_html().replace('#', '#ppci.programs.')
    parts.append('.. raw:: html\n')
    parts.extend(['    ' + line for line in toc_html.splitlines()])
    parts.append('')
    
    programs1, programs2, programs3 = programs.get_program_classes_by_group()
    
    # Add base classes
    parts.append('Base program classes')
    parts.append('-' * len(parts[-1]))
    parts.append('')
    for program in (programs.Program, programs.SourceCodeProgram,
                    programs.IntermediateProgram, programs.MachineProgram):
        parts.append('.. autoclass:: ppci.programs.{}'.format(program.__name__))
        parts.append('   :members:\n\n')
    
    # Add concrete classes
    parts.append('Source code programs')
    parts.append('-' * len(parts[-1]))
    parts.append('')
    for program in programs1:
        parts.append('.. autoclass:: ppci.programs.{}'.format(program.__name__))
        parts.append('   :members:\n\n')
    
    parts.append('Intermediate programs')
    parts.append('-' * len(parts[-1]))
    parts.append('')
    for program in programs2:
        parts.append('.. autoclass:: ppci.programs.{}'.format(program.__name__))
        parts.append('   :members:\n\n')
    
    parts.append('Machine code programs')
    parts.append('-' * len(parts[-1]))
    parts.append('')
    for program in programs3:
        parts.append('.. autoclass:: ppci.programs.{}'.format(program.__name__))
        parts.append('   :members:\n\n')
    
    files_to_remove.append(os.path.join('reference', 'programs.rst'))
    with open(os.path.join(DOC_DIR, 'reference', 'programs.rst'), 'wb') as f:
        f.write('\n'.join(parts).encode())


if __name__ == '__main__':
    write_programs_rst()
