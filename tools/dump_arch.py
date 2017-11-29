
""" Helper script to dump all information for an architecture """

import argparse
import html
from ppci import api
from ppci.arch import encoding

arch = api.get_arch('msp430')
arch = api.get_arch('x86_64')


def mkstr(s):
    if isinstance(s, str):
        return s
    elif isinstance(s, encoding.Operand):
        return '${}'.format(s._name)
    else:
        raise NotImplementedError()


filename = 'arch_info.html'
with open(filename, 'w') as f:
    print("""<html>
    <body>
    """, file=f)

    # Create a list:
    instructions = []
    for i in arch.isa.instructions:
        if not i.syntax:
            continue
        syntax = ''.join(mkstr(s) for s in i.syntax.syntax)
        instructions.append((syntax, i))

    print('<h1>Instructions</h1>', file=f)
    print('<p>{} instructions available</p>'.format(len(instructions)), file=f)
    print('<table border="1">', file=f)
    print('<tr><th>syntax</th><th>Class</th></tr>', file=f)
    for syntax, ins_class in sorted(instructions, key=lambda x: x[0]):
        print('<tr>'.format(), file=f)
        print('<td>{}</td>'.format(html.escape(syntax)), file=f)
        print('<td>{}</td>'.format(html.escape(str(ins_class))), file=f)
        print('</tr>'.format(), file=f)
    print('</table>', file=f)

    print("""</body>
    </html>
    """, file=f)
