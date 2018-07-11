
import re
from .nodes.visitor import Visitor


def required_padding(address, alignment):
    """ Return how many padding bytes are needed to align address """
    rest = address % alignment
    if rest:
        # We need padding bytes:
        return alignment - rest
    return 0


def print_ast(ast, file=None):
    """ Display an abstract syntax tree.
    """
    CAstPrinter(file=file).print(ast)


class CAstPrinter(Visitor):
    """ Print AST of a C program """
    def __init__(self, file=None):
        self.indent = 0
        self.file = file

    def print(self, node):
        self.visit(node)

    def _print(self, node):
        print('    ' * self.indent + str(node), file=self.file)

    def visit(self, node):
        self._print(node)
        self.indent += 1
        super().visit(node)
        self.indent -= 1


def cnum(txt: str):
    """ Convert C number to integer """
    assert isinstance(txt, str)

    # Lower tha casing:
    num = txt.lower()

    if '.' in txt:
        # Floating point
        type_specifiers = ['double']
        return float(num), type_specifiers
    else:
        # Integer:

        # Determine base:
        if num.startswith('0x'):
            num = num[2:]
            base = 16
        elif num.startswith('0b'):
            num = num[2:]
            base = 2
        elif num.startswith('0'):
            base = 8
        else:
            base = 10

        # Determine suffix:
        type_specifiers = []
        while num.endswith(('l', 'u')):
            if num.endswith('u'):
                num = num[:-1]
                type_specifiers.append('unsigned')
            elif num.endswith('l'):
                num = num[:-1]
                type_specifiers.append('long')
            else:
                raise NotImplementedError()

        if not type_specifiers:
            type_specifiers.append('int')

        # Take the integer:
        return int(num, base), type_specifiers


def replace_escape_codes(txt: str):
    """ Replace escape codes inside the given text """
    prog = re.compile(
        r'(\\[0-7]{1,3})|(\\x[0-9a-fA-F]+)|'
        r'(\\[\'"?\\abfnrtv])|(\\u[0-9a-fA-F]{4})|(\\U[0-9a-fA-F]{8})')
    pos = 0
    endpos = len(txt)
    parts = []
    while pos != endpos:
        # Find next match:
        mo = prog.search(txt, pos)
        if mo:
            # We have an escape code:
            if mo.start() > pos:
                parts.append(txt[pos:mo.start()])
            # print(mo.groups())
            octal, hx, ch, uni1, uni2 = mo.groups()
            if octal:
                char = chr(int(octal[1:], 8))
            elif hx:
                char = chr(int(hx[2:], 16))
            elif ch:
                mp = {
                    'a': '\a',
                    'b': '\b',
                    'f': '\f',
                    'n': '\n',
                    'r': '\r',
                    't': '\t',
                    'v': '\v',
                    '\\': '\\',
                    '"': '"',
                    "'": "'",
                    '?': '?',
                }
                char = mp[ch[1:]]
            elif uni1:
                char = chr(int(uni1[2:], 16))
            elif uni2:
                char = chr(int(uni2[2:], 16))
            else:  # pragma: no cover
                raise RuntimeError()
            parts.append(char)
            pos = mo.end()
        else:
            # No escape code found:
            parts.append(txt[pos:])
            pos = endpos
    return ''.join(parts)


def charval(txt: str):
    """ Get the character value of a char literal """
    # Wide char?
    if txt.startswith('L'):
        txt = txt[1:]

    # Strip out ' and '
    assert txt[0] == "'"
    assert txt[-1] == "'"
    txt = txt[1:-1]
    assert len(txt) == 1
    # TODO: implement wide characters!
    return ord(txt), ['char']
