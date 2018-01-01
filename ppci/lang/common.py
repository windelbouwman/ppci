from collections import namedtuple
import os


class Token:
    """
        Token is used in the lexical analyzer. The lexical analyzer takes
        a text and splits it into tokens.
    """
    __slots__ = ['typ', 'val', 'loc']

    def __init__(self, typ, val, loc):
        self.typ = typ
        self.val = val
        assert isinstance(loc, SourceLocation)
        self.loc = loc

    def __repr__(self):
        return 'Token({}, {}, {})'.format(self.typ, self.val, self.loc)


class SourceLocation:
    """ A location that refers to a position in a source file """
    __slots__ = ['filename', 'row', 'col', 'length', 'source']

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
        if not self.source and self.filename:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.source = f.read()

        if self.source:
            lines = self.source.split('\n')
            return lines[self.row-1]
        else:
            return "Could not load source"

    def print_message(self, message, lines=None, filename=None, file=None):
        """ Print a message at this location in the given source lines """
        if lines is None:
            with open(self.filename, 'r') as f:
                src = f.read()
            lines = src.splitlines()

        # Print filename:
        if filename is None:
            filename = self.filename
        if filename:
            print('File : "{}"'.format(filename), file=file)

        # Print relevant lines:
        prerow = self.row - 2
        if prerow < 1:
            prerow = 1

        afterrow = self.row + 3
        if afterrow > len(lines):
            afterrow = len(lines)

        # print preceding source lines:
        for row in range(prerow, self.row):
            print_line(row, lines, file=file)

        # print source line containing error:
        print_line(self.row, lines, file=file)
        print(' '*(6+self.col-1) + '^ {0}'.format(message), file=file)

        # print trailing source line:
        for row in range(self.row + 1, afterrow + 1):
            print_line(row, lines, file=file)


def print_line(row, lines, file=None):
    """ Print a single source line """
    if row in range(len(lines)):
        txt = lines[row - 1]
        print('{:5}:{}'.format(row, txt), file=file)


SourceRange = namedtuple('SourceRange', ['p1', 'p2'])
