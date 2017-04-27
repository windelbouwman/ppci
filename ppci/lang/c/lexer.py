""" C Language lexer """

import logging
import io

from ...common import Token, SourceLocation, CompilerError


class CToken(Token):
    """ C token (including optional preceeding spaces) """
    def __init__(self, typ, val, space, first, loc):
        super().__init__(typ, val, loc)
        self.space = space
        self.first = first

    def __repr__(self):
        return 'CToken({}, {}, "{}", {})'.format(
            self.typ, self.val, self.space, self.loc)

    def __str__(self):
        return self.space + self.val

    def copy(self, space=None, first=None):
        """ Return a new token which is a mildly modified copy """
        if space is None:
            space = self.space
        if first is None:
            first = self.first
        return CToken(self.typ, self.val, space, first, self.loc)


class Char:
    """ Represents a single character with a location """
    def __init__(self, char, loc):
        self.char = char
        self.loc = loc

    def __repr__(self):
        return "CHAR '{}' at {}".format(self.char, self.loc)


def create_characters(f, filename):
    """ Create a sequence of characters """
    for row, line in enumerate(f):
        for col, char in enumerate(line):
            loc = SourceLocation(filename, row + 1, col + 1, 1)
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


class HandLexerBase:
    """ Base class for handwritten lexers based on an idea of Rob Pike.

    See also:
    http://eli.thegreenplace.net/2012/08/09/
    using-sub-generators-for-lexical-scanning-in-python/

    And:
    https://www.youtube.com/watch?v=HxaD_trXwRE
    """
    def __init__(self):
        self.token_buffer = []
        self.pushed_back = []
        self.current_text = []

    def tokenize(self, characters, start_state):
        """ Return a sequence of tokens """
        self.characters = characters
        state = start_state
        while state:
            while self.token_buffer:
                yield self.token_buffer.pop(0)
            state = state()

    def next_char(self) -> Char:
        if self.pushed_back:
            char = self.pushed_back.pop(0)
        else:
            char = next(self.characters, None)

        if char:
            self.current_text.append(char)

        return char

    def backup_char(self, char: Char):
        """ go back one item """
        if char:
            self.current_text.pop(-1)
            self.pushed_back.insert(0, char)

    def emit(self, typ):
        """ Emit the current text under scope as a token """
        val = ''.join(c.char for c in self.current_text)
        loc = self.current_text[0].loc
        token = Token(typ, val, loc)
        self.token_buffer.append(token)
        self.current_text.clear()

    def ignore(self):
        """ Ignore text under cursor """
        pass

    def accept(self, valid):
        """ Accept a single character if it is in the valid set """
        char = self.next_char()
        if char and char.char in valid:
            return True
        else:
            self.backup_char(char)
            return False

    def accept_run(self, valid):
        while self.accept(valid):
            pass

    def error(self, message):
        raise CompilerError()


class CLexer(HandLexerBase):
    """ Lexer used for the preprocessor """
    logger = logging.getLogger('clexer')
    double_glyphs = (
        '##', '&&', '||', '<<', '>>', '>=', '==', '<=', '::', '!=')

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
                return self.lex_linecomment
            elif self.accept('*'):
                return self.lex_blockcomment
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
                self.emit('<<')
            else:
                self.emit('<')
            return self.lex_c
        elif r.char == '>':
            if self.accept('='):
                self.emit('>=')
            elif self.accept('>'):
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
            else:
                self.emit('|')
            return self.lex_c
        elif r.char == '&':
            if self.accept('&'):
                self.emit('&&')
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
            else:
                self.emit('-')
            return self.lex_c
        elif r.char == '*':
            if self.accept('='):
                self.emit('*=')
            else:
                self.emit('*')
            return self.lex_c
        elif r.char in ';{}()[],.?%~:^':
            self.emit(r.char)
            return self.lex_c
        elif r.char == "\\":
            self.emit(r.char)
            return self.lex_c
        else:
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

        # Accept some suffixes:
        self.accept('LlUu')
        self.accept('LlUu')

        # self.accept('
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
        return self.lex_c

    def lex_blockcomment(self):
        while True:
            if self.accept('*'):
                if self.accept('/'):
                    break
            else:
                self.next_char()
        return self.lex_c

    def lex_string(self):
        """ Scan for a complete string """
        c = self.next_char()
        while c and c.char != '"':
            c = self.next_char()
        self.emit('STRING')
        return self.lex_c

    def lex_char(self):
        """ Scan for a complete character constant """
        if self.accept("\\"):
            self.next_char()
        else:
            self.next_char()

        if not self.accept("'"):
            self.error("Expected ' ")

        self.emit('CHAR')
        return self.lex_c
