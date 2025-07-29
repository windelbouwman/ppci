from collections import namedtuple
import os


class Token:
    """
    Token is used in the lexical analyzer. The lexical analyzer takes
    a text and splits it into tokens.
    """

    __slots__ = ["typ", "val", "loc"]

    def __init__(self, typ, val, loc):
        self.typ = typ
        self.val = val
        assert isinstance(loc, SourceLocation)
        self.loc = loc

    def __repr__(self):
        return "Token({}, {}, {})".format(self.typ, self.val, self.loc)


class SourceLocation:
    """A location that refers to a position in a source file"""

    __slots__ = ["filename", "row", "col", "length", "source"]

    def __init__(self, filename, row, col, ln, source=None):
        self.filename = filename
        self.row = row
        self.col = col
        self.length = ln
        self.source = source

    def __repr__(self):
        return f"({self.filename}, {self.row}, {self.col}, {self.length})"

    def get_source_line(self):
        """Return the source line indicated by this location"""
        if not self.source and self.filename:
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    self.source = f.read()

        if self.source:
            lines = self.source.split("\n")
            return lines[self.row - 1]
        else:
            return "Could not load source"

    def print_message(
        self, message: str, lines=None, filename=None, file=None
    ):
        """Print a message at this location in the given source lines"""
        if lines is None:
            with open(self.filename, "r") as f:
                src = f.read()
            lines = src.splitlines()

        # Print filename:
        if filename is None:
            filename = self.filename
        if filename:
            print('File : "{}"'.format(filename), file=file)

        print_message(
            lines, self.row, self.col, self.length, message, file=file
        )


def print_message(
    lines, row: int, col: int, length: int, message: str, file=None
):
    """Render a message nicely embedded in surrounding source"""
    # Print relevant lines:
    prerow = row - 2
    if prerow < 1:
        prerow = 1

    afterrow = row + 3
    if afterrow > len(lines):
        afterrow = len(lines)

    # print preceding source lines:
    for r in range(prerow, afterrow + 1):
        # Render source line:
        if r in range(len(lines)):
            txt = lines[r - 1]
            print("{:5} :{}".format(r, txt), file=file)

        # print source line containing error:
        if r == row:
            base_txt = "      :"
            if length < 1:
                length = 1
            marker = "^" * length
            indent1_txt = base_txt + " " * (col - 1)
            indent2_txt = indent1_txt + " " * (length // 2)
            print(f"{indent1_txt}{marker}", file=file)
            print(f"{indent2_txt}|", file=file)
            print(f"{indent2_txt}+---- {message}", file=file)


SourceRange = namedtuple("SourceRange", ["p1", "p2"])
