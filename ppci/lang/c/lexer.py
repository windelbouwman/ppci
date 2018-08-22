""" C Language lexer """

import logging
import io

from ..common import SourceLocation
from .token import CToken
from ..tools.handlexer import HandLexerBase, Char


def create_characters(f, filename):
    """ Create a sequence of characters """
    for row, line in enumerate(f, 1):
        line = line.expandtabs()
        for col, char in enumerate(line, 1):
            loc = SourceLocation(filename, row, col, 1)
            yield Char(char, loc)


def trigraph_filter(characters):
    """ Replace trigraphs in a character sequence """
    tri_map = {
        '=': '#',
        '(': '[',
        ')': ']',
        '<': '{',
        '>': '}',
        '-': '~',
        '!': '|',
        '/': '\\',
        "'": '^',
    }
    buf = []
    for char in characters:
        buf.append(char)
        if len(buf) >= 3:
            if buf[0].char == '?' and buf[1].char == '?' and \
                    buf[2].char in tri_map:
                loc = buf.pop(0).loc
                buf.pop(0)
                char = tri_map[buf.pop(0).char]
                yield Char(char, loc)
            else:
                yield buf.pop(0)

    for c in buf:
        yield c


def continued_lines_filter(characters):
    r""" Glue lines which end with a backslash '\' """
    backslash = None
    for char in characters:
        if backslash:
            if char.char in '\r\n':
                pass
            else:
                yield backslash
                yield char
            backslash = False
        else:
            if char.char == '\\':
                backslash = char
            else:
                yield char


def lex_text(text, coptions):
    """ Lex a piece of text """
    lexer = CLexer(coptions)
    return list(lexer.lex_text(text))


class CLexer(HandLexerBase):
    """ Lexer used for the preprocessor """
    logger = logging.getLogger('clexer')
    lower_letters = 'abcdefghijklmnopqrstuvwxyz'
    upper_letters = lower_letters.upper()
    binary_numbers = '01'
    octal_numbers = binary_numbers + '234567'
    numbers = octal_numbers + '89'
    hex_numbers = numbers + 'abcdefABCDEF'

    def __init__(self, coptions):
        super().__init__()
        self.coptions = coptions

    def lex(self, src, filename):
        """ Read a source and generate a series of tokens """
        self.logger.debug('Lexing %s', filename)

        characters = create_characters(src, filename)
        if self.coptions['trigraphs']:
            characters = trigraph_filter(characters)
        characters = continued_lines_filter(characters)
        # print('=== lex ')
        # print(s)
        # print('=== end lex ')

        # s = '\n'.join(r)
        return self.tokenize(characters)

    def lex_text(self, txt):
        """ Create tokens from the given text """
        f = io.StringIO(txt)
        filename = None
        characters = characters = create_characters(f, filename)
        return self.tokenize(characters)

    def tokenize(self, characters):
        """ Generate tokens from characters """
        space = ''
        first = True
        token = None
        for token in super().tokenize(characters, self.lex_c):
            if token.typ == 'BOL':
                if first:
                    # Yield an extra start of line
                    yield CToken('BOL', '', '', first, token.loc)
                first = True
                space = ''
            elif token.typ == 'WS':
                space += token.val
            else:
                yield CToken(token.typ, token.val, space, first, token.loc)
                space = ''
                first = False

        # Emit last newline:
        if first and token:
            # Yield an extra start of line
            yield CToken('BOL', '', '', first, token.loc)

    def lex_c(self):
        """ Root parsing function """
        r = self.next_char()
        if r is None:
            pass
        elif r.char == 'L':
            # Wide char or identifier
            if self.accept("'"):
                return self.lex_char
            else:
                return self.lex_identifier
        elif r.char in self.lower_letters + self.upper_letters + '_':
            return self.lex_identifier
        elif r.char in self.numbers:
            self.backup_char(r)
            return self.lex_number
        elif r.char in ' \t':
            return self.lex_whitespace
        elif r.char in '\n':
            self.emit('BOL')
            return self.lex_c
        elif r.char == '/':
            if self.accept('/'):
                if self.coptions['std'] == 'c89':
                    self.error('C++ style comments are not allowed in C90')
                return self.lex_linecomment
            elif self.accept('*'):
                return self.lex_blockcomment
            elif self.accept('='):
                self.emit('/=')
                return self.lex_c
            else:
                self.emit('/')
                return self.lex_c
        elif r.char == '"':
            return self.lex_string
        elif r.char == "'":
            return self.lex_char
        elif r.char == '<':
            if self.accept('='):
                self.emit('<=')
            elif self.accept('<'):
                if self.accept('='):
                    self.emit('<<')
                else:
                    self.emit('<<')
            else:
                self.emit('<')
            return self.lex_c
        elif r.char == '>':
            if self.accept('='):
                self.emit('>=')
            elif self.accept('>'):
                if self.accept('='):
                    self.emit('>>=')
                else:
                    self.emit('>>')
            else:
                self.emit('>')
            return self.lex_c
        elif r.char == '=':
            if self.accept('='):
                self.emit('==')
            else:
                self.emit('=')
            return self.lex_c
        elif r.char == '!':
            if self.accept('='):
                self.emit('!=')
            else:
                self.emit('!')
            return self.lex_c
        elif r.char == '|':
            if self.accept('|'):
                self.emit('||')
            elif self.accept('='):
                self.emit('|=')
            else:
                self.emit('|')
            return self.lex_c
        elif r.char == '&':
            if self.accept('&'):
                self.emit('&&')
            elif self.accept('='):
                self.emit('&=')
            else:
                self.emit('&')
            return self.lex_c
        elif r.char == '#':
            if self.accept('#'):
                self.emit('##')
            else:
                self.emit('#')
            return self.lex_c
        elif r.char == '+':
            if self.accept('+'):
                self.emit('++')
            elif self.accept('='):
                self.emit('+=')
            else:
                self.emit('+')
            return self.lex_c
        elif r.char == '-':
            if self.accept('-'):
                self.emit('--')
            elif self.accept('='):
                self.emit('-=')
            elif self.accept('>'):
                self.emit('->')
            else:
                self.emit('-')
            return self.lex_c
        elif r.char == '*':
            if self.accept('='):
                self.emit('*=')
            else:
                self.emit('*')
            return self.lex_c
        elif r.char == '%':
            if self.accept('='):
                self.emit('%=')
            else:
                self.emit('%')
            return self.lex_c
        elif r.char == '^':
            if self.accept('='):
                self.emit('^=')
            else:
                self.emit('^')
            return self.lex_c
        elif r.char == '~':
            if self.accept('='):
                self.emit('~=')
            else:
                self.emit('~')
            return self.lex_c
        elif r.char == '.':
            if self.accept_sequence(['.', '.']):
                self.emit('...')
            elif self.accept(self.numbers):
                # We got .[0-9]
                return self.lex_float
            else:
                self.emit('.')
            return self.lex_c
        elif r.char in ';{}()[],?:':
            self.emit(r.char)
            return self.lex_c
        elif r.char == "\\":
            self.emit(r.char)
            return self.lex_c
        else:  # pragma: no cover
            raise NotImplementedError(r)

    def lex_identifier(self):
        id_chars = self.lower_letters + self.upper_letters + self.numbers + '_'
        self.accept_run(id_chars)
        self.emit('ID')
        return self.lex_c

    def lex_number(self):
        if self.accept('0'):
            # Octal, binary or hex!
            if self.accept('xX'):
                number_chars = self.hex_numbers
            elif self.accept('bB'):
                number_chars = self.binary_numbers
            else:
                number_chars = self.octal_numbers
        else:
            number_chars = self.numbers

        # Accept a series of number characters:
        self.accept_run(number_chars)
        if self.accept('.'):
            return self.lex_float()
        else:
            # Accept some suffixes:
            self.accept('LlUu')
            self.accept('LlUu')
            # TODO: handle suffixes better
            self.accept('LlUu')

            # self.accept('
            self.emit('NUMBER')
            return self.lex_c

    def lex_float(self):
        self.accept_run(self.numbers)
        if self.accept('eEpP'):
            self.accept('+-')
            self.accept_run(self.numbers)

        self.emit('NUMBER')
        return self.lex_c

    def lex_whitespace(self):
        self.accept_run(' \t')
        self.emit('WS')
        return self.lex_c

    def lex_linecomment(self):
        c = self.next_char()
        while c and c.char != '\n':
            c = self.next_char()
        self.backup_char(c)
        self.ignore()
        return self.lex_c

    def lex_blockcomment(self):
        while True:
            if self.accept('*'):
                if self.accept('/'):
                    self.ignore()
                    # self.emit('WS')
                    break
            else:
                self.next_char(eof=False)
        return self.lex_c

    def lex_string(self):
        """ Scan for a complete string """
        c = self.next_char(eof=False)
        while c.char != '"':
            if c.char == '\\':
                self._handle_escape_character()
            c = self.next_char(eof=False)
        self.emit('STRING')
        return self.lex_c

    def lex_char(self):
        """ Scan for a complete character constant """
        if self.accept("\\"):
            self._handle_escape_character()
        else:
            # Normal char:
            self.next_char(eof=False)

        self.expect("'")

        self.emit('CHAR')
        return self.lex_c

    def _handle_escape_character(self):
        # Escape char!
        if self.accept("'\"?\\abfnrtv"):
            pass
        elif self.accept(self.octal_numbers):
            self.accept(self.octal_numbers)
            self.accept(self.octal_numbers)
        elif self.accept('x'):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        elif self.accept('u'):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        elif self.accept('U'):
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
            self.accept(self.hex_numbers)
        else:
            self.error('Unexpected escape character')
