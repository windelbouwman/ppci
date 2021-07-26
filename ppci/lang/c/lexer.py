""" C Language lexer """

import logging
import io

from .token import CToken
from ..tools.handlexer import HandLexerBase


class SourceFile:
    """ Presents the current file. """

    def __init__(self, name):
        self.filename = name
        self.row = 1

    def __repr__(self):
        return "<SourceFile at {}:{}>".format(self.filename, self.row)


tri_map = {
    "=": "#",
    "(": "[",
    ")": "]",
    "<": "{",
    ">": "}",
    "-": "~",
    "!": "|",
    "/": "\\",
    "'": "^",
}


def trigraph_filter(chunks):
    """ Replace trigraphs in a chunk sequence """

    for row, column, text in chunks:
        if len(text) > 2:
            j = i = 0

            while i < len(text) - 2:
                if (
                    text[i] == "?"
                    and text[i + 1] == "?"
                    and text[i + 2] in tri_map
                ):
                    char = tri_map[text[i + 2]]
                    if j < i:
                        yield (row, column + j, text[j:i])
                    yield (row, column + i, char)
                    j = i = i + 3
                else:
                    i += 1
            if j < len(text):
                yield (row, column + j, text[j:])
        else:
            yield (row, column, text)


def continued_lines_filter(chunks):
    r""" Glue lines which end with a backslash '\' """
    backslash = None
    for row, column, text in chunks:
        if backslash:
            # Assume here that text does not start with a newline.
            if text in "\r\n":
                row, column, text = backslash
                if len(text) > 1:
                    yield row, column, text[:-1]
            else:
                yield backslash
                yield row, column, text
            backslash = False
        else:
            if text.endswith("\\"):
                backslash = row, column, text
            elif text.endswith("\\\r") or text.endswith("\\\n"):
                yield row, column, text[:-2]
            else:
                yield row, column, text

    if backslash:
        yield backslash


def lex_text(text, coptions):
    """ Lex a piece of text """
    lexer = CLexer(coptions)
    return list(lexer.lex_text(text))


class CLexer(HandLexerBase):
    """ Lexer used for the preprocessor """

    logger = logging.getLogger("clexer")
    lower_letters = "abcdefghijklmnopqrstuvwxyz"
    upper_letters = lower_letters.upper()
    binary_numbers = "01"
    octal_numbers = binary_numbers + "234567"
    numbers = octal_numbers + "89"
    hex_numbers = numbers + "abcdefABCDEF"

    def __init__(self, coptions):
        super().__init__()
        self.coptions = coptions

    def lex(self, src, source_file):
        """ Read a source and generate a series of tokens """
        self.logger.debug("Lexing %s", source_file.filename)

        self._source_file = source_file
        self._filename = source_file.filename
        chunks = self.create_chunks(src)
        if self.coptions["trigraphs"]:
            chunks = trigraph_filter(chunks)
        chunks = continued_lines_filter(chunks)
        # print('=== lex ')
        # print(s)
        # print('=== end lex ')

        # s = '\n'.join(r)
        return self.tokenize(source_file.filename, chunks)

    def lex_text(self, txt):
        """ Create tokens from the given text """
        f = io.StringIO(txt)
        filename = None
        source_file = SourceFile(filename)
        return self.lex(f, source_file)

    def tokenize(self, filename, chunks):
        """ Generate tokens from characters """
        space = ""
        first = True
        token = None
        for token in super().tokenize(filename, chunks, self.lex_c):
            if token.typ == "BOL":
                if first:
                    # Yield an extra start of line
                    yield CToken("BOL", "", "", first, token.loc)
                first = True
                space = ""
            elif token.typ == "WS":
                space += token.val
            else:
                yield CToken(token.typ, token.val, space, first, token.loc)
                space = ""
                first = False

        # Emit last newline:
        if first and token:
            # Yield an extra start of line
            yield CToken("BOL", "", "", first, token.loc)

    def create_chunks(self, f):
        """ Create a sequence of chunks.

        Each chunk is a tuple of (row, column, text)
        """
        for line in f:
            # TODO: expand tabs brakes the column info..
            line = line.expandtabs()
            yield (self._source_file.row, 1, line)
            self._source_file.row += 1

    def lex_c(self):
        """ Root parsing function """
        char = self.next_char()

        if char is None:
            pass
        elif char == "L":
            # Wide char or identifier
            if self.accept("'"):
                return self.lex_char
            else:
                return self.lex_identifier
        elif char in self.lower_letters + self.upper_letters + "_":
            return self.lex_identifier
        elif char in self.numbers:
            self.backup_char(char)
            return self.lex_number
        elif char in " \t":
            return self.lex_whitespace
        elif char in "\n":
            self.emit("BOL")
            return self.lex_c
        elif char == "\f":
            # Skip form feed ^L chr(0xc) character
            self.ignore()
            return self.lex_c
        elif char == "/":
            if self.accept("/"):
                if self.coptions["std"] == "c89":
                    self.error("C++ style comments are not allowed in C90")
                return self.lex_linecomment
            elif self.accept("*"):
                return self.lex_blockcomment
            elif self.accept("="):
                self.emit("/=")
                return self.lex_c
            else:
                self.emit("/")
                return self.lex_c
        elif char == '"':
            return self.lex_string
        elif char == "'":
            return self.lex_char
        elif char == "<":
            if self.accept("="):
                self.emit("<=")
            elif self.accept("<"):
                if self.accept("="):
                    self.emit("<<")
                else:
                    self.emit("<<")
            else:
                self.emit("<")
            return self.lex_c
        elif char == ">":
            if self.accept("="):
                self.emit(">=")
            elif self.accept(">"):
                if self.accept("="):
                    self.emit(">>=")
                else:
                    self.emit(">>")
            else:
                self.emit(">")
            return self.lex_c
        elif char == "=":
            if self.accept("="):
                self.emit("==")
            else:
                self.emit("=")
            return self.lex_c
        elif char == "!":
            if self.accept("="):
                self.emit("!=")
            else:
                self.emit("!")
            return self.lex_c
        elif char == "|":
            if self.accept("|"):
                self.emit("||")
            elif self.accept("="):
                self.emit("|=")
            else:
                self.emit("|")
            return self.lex_c
        elif char == "&":
            if self.accept("&"):
                self.emit("&&")
            elif self.accept("="):
                self.emit("&=")
            else:
                self.emit("&")
            return self.lex_c
        elif char == "#":
            if self.accept("#"):
                self.emit("##")
            else:
                self.emit("#")
            return self.lex_c
        elif char == "+":
            if self.accept("+"):
                self.emit("++")
            elif self.accept("="):
                self.emit("+=")
            else:
                self.emit("+")
            return self.lex_c
        elif char == "-":
            if self.accept("-"):
                self.emit("--")
            elif self.accept("="):
                self.emit("-=")
            elif self.accept(">"):
                self.emit("->")
            else:
                self.emit("-")
            return self.lex_c
        elif char == "*":
            if self.accept("="):
                self.emit("*=")
            else:
                self.emit("*")
            return self.lex_c
        elif char == "%":
            if self.accept("="):
                self.emit("%=")
            else:
                self.emit("%")
            return self.lex_c
        elif char == "^":
            if self.accept("="):
                self.emit("^=")
            else:
                self.emit("^")
            return self.lex_c
        elif char == "~":
            if self.accept("="):
                self.emit("~=")
            else:
                self.emit("~")
            return self.lex_c
        elif char == ".":
            if self.accept(self.numbers):
                # We got .[0-9]
                return self.lex_float
            elif self.accept("."):
                if self.accept('.'):
                    self.emit("...")
                else:
                    self.error('Expected . or ...')
            else:
                self.emit(".")
            return self.lex_c
        elif char in ";{}()[],?:":
            self.emit(char)
            return self.lex_c
        elif char == "\\":
            self.emit(char)
            return self.lex_c
        else:  # pragma: no cover
            raise NotImplementedError(char)

    def lex_identifier(self):
        id_chars = self.lower_letters + self.upper_letters + self.numbers + "_"
        self.accept_run(id_chars)
        self.emit("ID")
        return self.lex_c

    def lex_number(self):
        """ Lex a single numeric literal. """
        if self.accept("0"):
            # Octal, binary or hex!
            if self.accept("xX"):
                number_chars = self.hex_numbers
                base = 16
            elif self.accept("bB"):
                number_chars = self.binary_numbers
                base = 2
            elif self.accept("."):
                return self.lex_float()
            else:
                number_chars = self.octal_numbers
                base = 8
        else:
            number_chars = self.numbers
            base = 10

        # Accept a series of number characters:
        self.accept_run(number_chars)
        if base == 10 and self.accept("."):
            # For example 12.3
            return self.lex_float()
        elif base == 10 and self.accept("eEpP"):
            # For example 12e7
            return self.lex_float()
        else:
            # Accept some integer suffixes, such as 'L', or 'ull'
            long_suffixes = 0
            unsigned_suffixes = 0
            while long_suffixes < 2 or unsigned_suffixes < 1:
                if long_suffixes < 2 and self.accept("lL"):
                    long_suffixes += 1
                elif unsigned_suffixes < 1 and self.accept("uU"):
                    unsigned_suffixes += 1
                else:
                    break

            self.emit("NUMBER")
            return self.lex_c

    def lex_float(self):
        """ Lex floating point number from decimal dot onwards. """
        self.accept_run(self.numbers)
        if self.accept("eEpP"):
            self.accept("+-")
            self.accept_run(self.numbers)

        self.emit("FLOAT")
        return self.lex_c

    def lex_whitespace(self):
        self.accept_run(" \t")
        self.emit("WS")
        return self.lex_c

    def lex_linecomment(self):
        c = self.next_char()
        while c and c != "\n":
            c = self.next_char()
        self.backup_char(c)
        self.ignore()
        return self.lex_c

    def lex_blockcomment(self):
        while True:
            if self.accept("*"):
                if self.accept("/"):
                    self.ignore()
                    # self.emit('WS')
                    break
            else:
                self.next_char(eof=False)
        return self.lex_c

    def lex_string(self):
        """ Scan for a complete string """
        c = self.next_char(eof=False)
        while c != '"':
            if c == "\\":
                self._handle_escape_character()
            c = self.next_char(eof=False)
        self.emit("STRING")
        return self.lex_c

    def lex_char(self):
        """ Scan for a complete character constant """
        if self.accept("\\"):
            self._handle_escape_character()
        else:
            # Normal char:
            self.next_char(eof=False)

        self.expect("'")

        self.emit("CHAR")
        return self.lex_c

    def _handle_escape_character(self):
        # Escape char!
        if self.accept("'\"?\\abfnrtve"):
            pass
        elif self.accept(self.octal_numbers):
            self.accept(self.octal_numbers)
            self.accept(self.octal_numbers)
        elif self.accept("x"):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        elif self.accept("u"):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        elif self.accept("U"):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        else:
            self.error("Unexpected escape character")
