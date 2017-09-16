"""
   Error handling routines
   Diagnostic utils
   Source location structures
"""


import logging
from .lang.common import SourceLocation


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


def get_file(f, mode='r'):
    """ Determine if argument is a file like object or make it so! """
    if hasattr(f, 'read'):
        # Assume this is a file like object
        return f
    elif isinstance(f, str):
        return open(f, mode)
    else:
        raise FileNotFoundError('Cannot open {}'.format(f))


class CompilerError(Exception):
    def __init__(self, msg, loc=None):
        # super().__init__()
        self.msg = msg
        self.loc = loc
        if loc:
            assert isinstance(loc, SourceLocation), \
                   '{0} must be SourceLocation'.format(type(loc))

    def __repr__(self):
        return '"{}"'.format(self.msg)

    def render(self, lines):
        """ Render this error in some lines of context """
        self.loc.print_message('Error: {0}'.format(self.msg), lines=lines)

    def print(self, file=None):
        """ Print the error inside some nice context """
        if self.loc:
            self.loc.print_message(self.msg, file=file)
        else:
            print(self.msg, file=file)


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
        self.logger.debug('Adding source, filename="%s"', name)
        self.sources[name] = src

    def add_diag(self, d):
        """ Add a diagnostic message """
        if d.loc:
            self.logger.error('Line %s: %s', d.loc.row, d.msg)
        else:
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
