
from ...common import CompilerError


def make_comma_or(parts):
    parts = list(map(lambda x: '"{}"'.format(x), parts))
    if len(parts) > 1:
        last = parts[-1]
        first = parts[:-1]
        return ', '.join(first) + ' or ' + last
    else:
        return ''.join(parts)


class RecursiveDescentParser:
    """ Base class for recursive descent parsers """
    def __init__(self):
        self.token = None  # The current token under cursor
        self.tokens = None  # Iterable of tokens
        self._look_ahead = []
        self._last_loc = None

    def init_lexer(self, tokens):
        """ Initialize the parser with the given tokens (an iterator) """
        self.tokens = tokens
        self.token = next(self.tokens, None)
        self._look_ahead = []

    def error(self, msg, loc=None):
        """ Raise an error at the current location """
        if loc is None:
            if self.token is None:
                if self._last_loc is None:
                    loc = None
                else:
                    loc = self._last_loc
            else:
                loc = self.token.loc
        raise CompilerError(msg, loc)

    @property
    def current_location(self):
        return self.token.loc

    # Lexer helpers:
    def consume(self, typ=None):
        """ Assert that the next token is typ, and if so, return it.

        If typ is a list or tuple, consume one of the given types.
        If typ is not given, consume the next token.
        """
        if typ is None:
            typ = self.peek

        expected_types = typ if isinstance(typ, (list, tuple, set)) else [typ]

        if self.peek in expected_types:
            return self.next_token()
        else:
            expected = make_comma_or(expected_types)
            self.error(
                'Expected {0}, got "{1}"'.format(expected, self.peek))

    def has_consumed(self, typ):
        """ Checks if the look-ahead token is of type typ, and if so
            eats the token and returns true """
        if self.peek == typ:
            self.consume()
            return True
        return False

    def next_token(self):
        """ Advance to the next token """
        tok = self.token
        if self._look_ahead:
            self.token = self._look_ahead.pop(0)
        else:
            self.token = next(self.tokens, None)

        if self.token is None and tok is not None:
            self._last_loc = tok.loc

        return tok

    def not_impl(self, msg=''):  # pragma: no cover
        """ Call this function when parsing reaches unimplemented parts """
        raise CompilerError('Not implemented ' + msg, loc=self.token.loc)

    @property
    def peek(self):
        """ Look at the next token to parse without popping it """
        if self.token:
            return self.token.typ

    def look_ahead(self, amount):
        """ Take a look at x tokens ahead """
        if amount > 0:
            while len(self._look_ahead) < amount:
                next_token = next(self.tokens, None)
                if next_token is None:
                    return
                self._look_ahead.append(next_token)
            return self._look_ahead[amount - 1]
        else:
            return self.token

    @property
    def at_end(self):
        return self.peek is None
