"""
   Error handling routines
   Diagnostic utils
   Source location structures
"""


from collections import namedtuple
import logging
import os


logformat = '%(asctime)s | %(levelname)8s | %(name)10.10s | %(message)s'


def make_num(txt):
    if txt.startswith('0x'):
        return int(txt[2:], 16)
    elif txt.startswith('$'):
        return int(txt[1:], 16)
    elif txt.startswith('0b'):
        return int(txt[2:], 2)
    elif txt.startswith('%'):
        return int(txt[1:], 2)
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


def print_line(row, lines):
    """ Print a single source line """
    if row in range(len(lines)):
        txt = lines[row - 1]
        print('{:5}:{}'.format(row, txt))


class SourceLocation:
    """ A location that refers to a position in a source file """
    def __init__(self, filename, row, col, ln, source=None):
        self.filename = filename
        self.row = row
        self.col = col
        self.length = ln
        self.source = source

    def __repr__(self):
        return '({}, {}, {})'.format(self.filename, self.row, self.col)

    def get_source_line(self):
        """ Return the source line indicated by this location """
        if not self.source:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.source = f.read()
        if self.source:
            lines = self.source.split('\n')
            return lines[self.row-1]
        else:
            return "Could not load source"

    def print_message(self, message, lines=None):
        """ Print a message at this location in the given source lines """
        prerow = self.row - 2
        if prerow < 1:
            prerow = 1
        afterrow = self.row + 3
        if afterrow > len(lines):
            afterrow = len(lines)

        # print preceding source lines:
        for row in range(prerow, self.row):
            print_line(row, lines)

        # print source line containing error:
        print_line(self.row, lines)
        print(' '*(6+self.col-1) + '^ {0}'.format(message))

        # print trailing source line:
        for row in range(self.row + 1, afterrow + 1):
            print_line(row, lines)


SourceRange = namedtuple('SourceRange', ['p1', 'p2'])


class CompilerError(Exception):
    def __init__(self, msg, loc=None):
        self.msg = msg
        self.loc = loc
        if loc:
            assert type(loc) is SourceLocation, \
                   '{0} must be SourceLocation'.format(type(loc))

    def __repr__(self):
        return '"{}"'.format(self.msg)

    def render(self, lines):
        """ Render this error in some lines of context """
        self.loc.print_message('Error: {0}'.format(self.msg), lines=lines)


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
        if e.loc:
            if e.loc.filename not in self.sources:
                print('Error: {0}'.format(e))
                return
            print("File: {}".format(e.loc.filename))
            source = self.sources[e.loc.filename]
            lines = source.split('\n')
            e.render(lines)
        else:
            print('Error: {0}'.format(e))

        print('==============')
