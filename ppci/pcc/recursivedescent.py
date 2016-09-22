
from ..common import CompilerError


class RecursiveDescentParser:
    """ Base class for recursive descent parsers """
    def __init__(self):
        self.token = None
        self.tokens = None

    def init_lexer(self, tokens):
        self.tokens = tokens
        self.token = self.tokens.__next__()

    def error(self, msg, loc=None):
        """ Raise an error at the current location """
        if loc is None:
            loc = self.token.loc
        raise CompilerError(msg, loc)

    # Lexer helpers:
    def consume(self, typ=None):
        """ Assert that the next token is typ, and if so, return it. If
            typ is not given, consume the next token.
        """
        if typ is None:
            typ = self.peak
        if self.peak == typ:
            return self.next_token()
        else:
            self.error('Excected: "{0}", got "{1}"'.format(typ, self.peak))

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
        if tok.typ != 'EOF':
            self.token = self.tokens.__next__()
        return tok

    def not_impl(self):  # pragma: no cover
        """ Call this function when parsing reaches unimplemented parts """
        raise CompilerError('Not implemented', loc=self.token.loc)

    @property
    def peak(self):
        """ Look at the next token to parse without popping it """
        return self.token.typ

    @property
    def at_end(self):
        return self.peak == 'EOF'
