from collections import namedtuple
import logging

"""
   Error handling routines
   Diagnostic utils
   Source location structures
"""


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


class DiagnosticsManager:
    def __init__(self):
        self.diags = []
        self.sources = {}
        self.logger = logging.getLogger('diagnostics')

    def addSource(self, name, src):
        self.logger.debug('Adding source, filename="{}"'.format(name))
        self.sources[name] = src

    def addDiag(self, d):
        self.logger.error(str(d.msg))
        self.diags.append(d)

    def error(self, msg, loc):
        self.addDiag(CompilerError(msg, loc))

    def clear(self):
        del self.diags[:]
        self.sources.clear()

    def printErrors(self):
        if len(self.diags) > 0:
            print('{0} Errors'.format(len(self.diags)))
            for d in self.diags:
                self.printError(d)

    def printError(self, e):
        def printLine(row, txt):
            print(str(row) + ':' + txt)
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
                printLine(r, lines[r-1])
            # print source line containing error:
            printLine(ro, lines[ro-1])
            print(' '*(len(str(ro)+':')+co-1) + '^ Error: {0}'.format(e.msg))
            # print trailing source line:
            for r in range(ro+1, afterrow+1):
                printLine(r, lines[r-1])
        print('==============')
