"""
   Error handling routines
   Diagnostic utils
   Source location structures
"""


from collections import namedtuple
import logging


logformat = '%(asctime)s | %(levelname)8s | %(name)10.10s | %(message)s'


def make_num(txt):
    if txt.startswith('0x'):
        return int(txt[2:], 16)
    else:
        return int(txt)

str2int = make_num


class Token:
    """
        Token is used in the lexical analyzer. The lexical analyzer takes
        a text and splits it into tokens.
    """
    def __init__(self, typ, val, loc):
        self.typ = typ
        self.val = val
        assert type(loc) is SourceLocation
        self.loc = loc

    def __repr__(self):
        return 'Token({}, {}, {})'.format(self.typ, self.val, self.loc)


class SourceLocation:
    """ A location that refers to a position in a source file """
    def __init__(self, filename, row, col, ln):
        self.filename = filename
        self.row = row
        self.col = col
        self.length = ln

    def __repr__(self):
        return '({}, {}, {})'.format(self.filename, self.row, self.col)


SourceRange = namedtuple('SourceRange', ['p1', 'p2'])


class CompilerError(Exception):
    def __init__(self, msg, loc=None):
        self.msg = msg
        self.loc = loc
        if loc:
            assert type(loc) is SourceLocation, \
                   '{0} must be SourceLocation'.format(type(loc))
            self.row = loc.row
            self.col = loc.col
        else:
            self.row = self.col = 0

    def __repr__(self):
        return '"{}"'.format(self.msg)


class IrFormError(CompilerError):
    pass


class ParseError(CompilerError):
    pass


class DiagnosticsManager:
    def __init__(self):
        self.diags = []
        self.sources = {}
        self.logger = logging.getLogger('diagnostics')

    def add_source(self, name, src):
        """ Add a source for error reporting """
        self.logger.debug('Adding source, filename="{}"'.format(name))
        self.sources[name] = src

    def add_diag(self, d):
        """ Add a diagnostic message """
        self.logger.error(str(d.msg))
        self.diags.append(d)

    def error(self, msg, loc):
        self.add_diag(CompilerError(msg, loc))

    def clear(self):
        del self.diags[:]
        self.sources.clear()

    def print_errors(self):
        """ Print all errors reported """
        if len(self.diags) > 0:
            print('{0} Errors'.format(len(self.diags)))
            for d in self.diags:
                self.print_error(d)

    def print_line(self, row, lines):
        """ Print a single source line """
        if row in range(len(lines)):
            txt = lines[row - 1]
            print('{:5}:{}'.format(row, txt))

    def print_error(self, e):
        """ Print a single error in a nice formatted way """
        print('==============')
        if not e.loc:
            print('Error: {0}'.format(e))
        else:
            if e.loc.filename not in self.sources:
                print('Error: {0}'.format(e))
                return
            print("File: {}".format(e.loc.filename))
            source = self.sources[e.loc.filename]
            lines = source.split('\n')
            ro, co = e.row, e.col
            prerow = ro - 2
            if prerow < 1:
                prerow = 1
            afterrow = ro + 3
            if afterrow > len(lines):
                afterrow = len(lines)

            # print preceding source lines:
            for r in range(prerow, ro):
                self.print_line(r, lines)

            # print source line containing error:
            self.print_line(ro, lines)
            print(' '*(6+co-1) + '^ Error: {0}'.format(e.msg))

            # print trailing source line:
            for r in range(ro+1, afterrow+1):
                self.print_line(r, lines)
        print('==============')
