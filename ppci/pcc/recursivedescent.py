
from ..common import CompilerError


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
        self.token = None
        self.tokens = None

    def init_lexer(self, tokens):
        """ Initialize the parser with the given tokens (an iterator) """
        self.tokens = tokens
        self.token = next(self.tokens, None)

    def error(self, msg, loc=None):
        """ Raise an error at the current location """
        if loc is None:
            loc = self.token.loc
        raise CompilerError(msg, loc)

    # Lexer helpers:
    def consume(self, typ=None):
        """ Assert that the next token is typ, and if so, return it.

        If typ is a list or tuple, consume one of the given types.
        If typ is not given, consume the next token.
        """
        if typ is None:
            typ = self.peak

        expected_types = typ if isinstance(typ, (list, tuple)) else [typ]

        if self.peak in expected_types:
            return self.next_token()
        else:
            expected = make_comma_or(expected_types)
            self.error(
                'Expected {0}, got "{1}"'.format(expected, self.peak))

    def has_consumed(self, typ):
        """ Checks if the look-ahead token is of type typ, and if so
            eats the token and returns true """
        if self.peak == typ:
            self.consume()
            return True
        return False

    def next_token(self):
        """ Advance to the next token """
        tok = self.token
        self.token = next(self.tokens, None)
        return tok

    def not_impl(self):  # pragma: no cover
        """ Call this function when parsing reaches unimplemented parts """
        raise CompilerError('Not implemented', loc=self.token.loc)

    @property
    def peak(self):
        """ Look at the next token to parse without popping it """
        if self.token:
            return self.token.typ

    @property
    def at_end(self):
        return self.peak is None
