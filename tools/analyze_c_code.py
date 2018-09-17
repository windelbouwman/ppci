
""" Analyze legacy C sourcecode.

This tool should help in understanding existing legacy C code better.


"""


import logging
import argparse
from ppci.lang.c import COptions, create_ast
from ppci.lang.c.nodes import declarations
from ppci.api import get_arch
from ppci.common import CompilerError
import glob
import os
import io
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import HtmlFormatter


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
LIBC_INCLUDES = os.path.join(THIS_DIR, '..', 'librt', 'libc')
logger = logging.getLogger('c-analyzer')


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('source_dir')
    args = parser.parse_args()
    defines = {
    }
    analyze_sources(args.source_dir, defines)


def get_tag(filename):
    return os.path.splitext(os.path.split(filename)[1])[0]


def analyze_sources(source_dir, defines):
    """ Analyze a directory with sourcecode """

    # Phase 1: acquire ast's:
    arch_info = get_arch('x86_64').info
    coptions = COptions()
    # TODO: infer defines from code:
    coptions.add_define('FPM_DEFAULT')
    coptions.add_include_path(source_dir)
    coptions.add_include_path(LIBC_INCLUDES)
    asts = []
    for source_filename in glob.iglob(os.path.join(source_dir, '*.c')):
        logger.info('Processing %s', source_filename)
        with open(source_filename, 'r') as f:
            source_code = f.read()
        f = io.StringIO(source_code)
        # ast = parse_text(source_code)
        try:
            ast = create_ast(
                f, arch_info, filename=source_filename, coptions=coptions)
            asts.append((source_filename, source_code, ast))
            # break
        except CompilerError as ex:
            print('Compiler error:', ex)
    logger.info("Got %s ast's", len(asts))

    # Phase 2: do some bad-ass analysis:
    global_variables = []
    functions = []
    for source_filename, source_code, ast in asts:
        for decl in ast.declarations:
            if isinstance(decl, declarations.VariableDeclaration):
                global_variables.append(decl)
            elif isinstance(decl, declarations.FunctionDeclaration):
                if decl.body is not None and decl.storage_class != 'static':
                    functions.append(decl)

    functions.sort(key=lambda d: d.name)

    # Phase 3: generate html report?
    with open('analyze_report.html', 'w') as f:
        c_lexer = CLexer()
        formatter = HtmlFormatter(lineanchors='fubar', linenos='inline')
        print('''<html>
        <head>
        <style>
        {}
        </style>
        </head>
        <body>
        '''.format(formatter.get_style_defs()), file=f)

        print('<h1>Overview</h1>', file=f)
        print('<table>', file=f)
        print(
            '<tr><th>Name</th><th>Location</th><th>typ</th></tr>',
            file=f)
        for func in functions:
            tagname = get_tag(func.location.filename)
            name = '<a href="#{2}-{1}">{0}</a>'.format(func.name, func.location.row, tagname)
            print(
                '<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>'.format(
                    name, '', ''),
                file=f)

        print('</table>', file=f)
        print('<h1>Files</h1>', file=f)

        for source_filename, source_code, ast in asts:
            tagname = get_tag(source_filename)
            formatter = HtmlFormatter(lineanchors=tagname, linenos='inline')
            print('<h2>{}</h2>'.format(source_filename), file=f)
            print('<table>', file=f)
            print(
                '<tr><th>Name</th><th>Location</th><th>typ</th></tr>',
                file=f)
            for decl in ast.declarations:
                if isinstance(decl, declarations.VariableDeclaration):
                    tp = 'var'
                elif isinstance(decl, declarations.FunctionDeclaration):
                    tp = 'func'
                else:
                    tp = 'other'

                tp += str(decl.storage_class)

                if source_filename == decl.location.filename:
                    name = '<a href="#{2}-{1}">{0}</a>'.format(decl.name, decl.location.row, tagname)
                else:
                    name = decl.name

                print(
                    '<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                        name, decl.location, tp),
                    file=f)
            print('</table>', file=f)
            print('''  <div>''', file=f)
            print(highlight(source_code, c_lexer, formatter), file=f)
            print('''  </div>''', file=f)

        print('''</body>
        </html>
        ''', file=f)


if __name__ == '__main__':
    main()
