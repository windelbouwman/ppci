
from ..common import Token
from ...common import CompilerError


class Char:
    """ Represents a single character with a location """
    def __init__(self, char, loc):
        self.char = char
        self.loc = loc

    def __repr__(self):
        return "CHAR '{}' at {}".format(self.char, self.loc)


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

    def next_char(self, eof=True) -> Char:
        """ Retrieve next character.

        If eof is False, raise an error when end of file is encountered.
        """
        if self.pushed_back:
            char = self.pushed_back.pop(0)
        else:
            char = next(self.characters, None)

        if char:
            self.current_text.append(char)

        if not eof and char is None:
            self.error('Expected a character, but at end of file')

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
        self.current_text.clear()

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

    def accept_sequence(self, sequence):
        """ Munch the exact given sequence of characters """
        chars = []
        for valid in sequence:
            char = self.next_char()
            chars.append(char)
            if char and char.char in valid:
                continue
            else:
                # Retreat! Pull back! We are wrong!
                for char in reversed(chars):
                    self.backup_char(char)
                return False
        return True

    def error(self, message):
        char = self.next_char()
        loc = None if char is None else char.loc
        raise CompilerError(message, loc)

    def expect(self, valid):
        if not self.accept(valid):
            self.error("Expected {}".format(', '.join(valid)))
