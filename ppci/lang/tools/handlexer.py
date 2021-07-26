""" Hand written lexer.

The idea of lexers is to split the sourcecode into chunks.

Chunks consists of a tuple (row, column, text)

A source file can be split up into a sequence of these chunks.

A cursor is a pointer to a specific character in the chunk sequence.

"""

from ..common import Token, SourceLocation
from ...common import CompilerError


class HandLexerBase:
    """Base class for handwritten lexers based on an idea of Rob Pike.

    See also:
    http://eli.thegreenplace.net/2012/08/09/
    using-sub-generators-for-lexical-scanning-in-python/

    And:
    https://www.youtube.com/watch?v=HxaD_trXwRE
    """

    def __init__(self):
        self.token_buffer = []  # emitted tokens
        self.current_text = []
        self._start_loc = None
        self._chunk = None
        self._chunk_index = 0
        self._chunk_start = 0

    def tokenize(self, filename, chunks, start_state):
        """ Return a sequence of tokens """
        self._filename = filename
        self._chunk_iter = iter(chunks)
        self._next_chunk()
        self._mark_start()
        state = start_state
        while state:
            while self.token_buffer:
                yield self.token_buffer.pop(0)
            state = state()

    def next_char(self, eof=True):
        """Retrieve next character.

        If eof is False, raise an error when end of file is encountered.
        """
        char = self._get_char()

        if not eof and char is None:
            self.error("Expected a character, but at end of file")

        return char

    def backup_char(self, char):
        """ go back one item """
        if char:
            assert self._chunk_index > 0
            self._chunk_index -= 1

    def get_chunk(self):
        """ Retrieve the next chunk of text

        This function must be implemented by subclasses.

        Must yield tuples of: (row, column, text)

        """
        return next(self._chunk_iter, None)

    def _get_char(self):
        if self._chunk:
            if self._chunk_index < len(self._chunk[2]):
                c = self._chunk[2][self._chunk_index]
                self._chunk_index += 1
            else:
                self._next_chunk()
                c = self._get_char()
        else:
            c = None
        return c

    def get_location(self):
        """ Return current location.
        """
        if self._chunk:
            row = self._chunk[0]
            column = self._chunk[1] + self._chunk_index
            return SourceLocation(self._filename, row, column, 1)

    def _next_chunk(self):
        """ Enter next text chunk. """
        if self._chunk:
            text = self._chunk[2][self._chunk_start:]
            self.current_text.append(text)
        self._chunk = self.get_chunk()
        self._chunk_index = 0
        self._chunk_start = 0

    def _mark_start(self):
        """ Store location, and reset text buffer. """
        self._start_loc = self.get_location()
        self.current_text.clear()
        self._chunk_start = self._chunk_index

    def emit(self, typ):
        """ Emit the current text under scope as a token """
        # Check if we have some text in this chunk:
        if self._chunk_index > self._chunk_start:
            text = self._chunk[2][self._chunk_start:self._chunk_index]
            self.current_text.append(text)
        # Grab all pieces of text from start to here:
        val = "".join(self.current_text)
        location = self._start_loc
        assert location
        token = Token(typ, val, location)
        self.token_buffer.append(token)
        self._mark_start()

    def ignore(self):
        """ Ignore text under cursor """
        self._mark_start()

    def accept(self, valid):
        """ Accept a single character if it is in the valid set """
        char = self.next_char()
        if char and char in valid:
            return True
        else:
            self.backup_char(char)
            return False

    def accept_run(self, valid):
        while self.accept(valid):
            pass

    def error(self, message):
        location = self.get_location()
        raise CompilerError(message, location)

    def expect(self, valid):
        if not self.accept(valid):
            self.error("Expected {}".format(", ".join(valid)))
