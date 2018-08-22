""" Module to assist in parsing nested tuple structures.

"""

import enum


class TupleParser:
    """ Helper class to parse tuple structures. """
    # match helper section:
    def _feed(self, t):
        self._nxt_func = self._tuple_generator(t)
        self._nxt = []

    def _tuple_generator(self, t):
        for e in self._tuple_generator_inner(t):
            yield e
        yield Token.EOF

    def _tuple_generator_inner(self, t):
        yield Token.LPAR
        for e in t:
            if isinstance(e, tuple):
                for e2 in self._tuple_generator_inner(e):
                    yield e2
            else:
                yield e
        yield Token.RPAR

    def _lookahead(self, amount: int):
        """ Return some lookahead tokens """
        assert amount > 0
        while len(self._nxt) < amount:
            nxt = next(self._nxt_func, Token.EOF)
            self._nxt.append(nxt)
        return tuple(self._nxt[:amount])

    def expect(self, *args):
        """ Check if tokens ahead match the given sequence """
        for arg in args:
            actual = self.take()
            if actual != arg:
                raise ValueError('Expected {} but have {}'.format(
                    arg, actual))

    def munch(self, *args):
        """ Match and eat tokens """
        if self.match(*args):
            self.expect(*args)
            return True
        else:
            return False

    def match(self, *args):
        """ Check if the given tokens are ahead """
        peek = self._lookahead(len(args))
        if peek == args:
            return True
        else:
            return False

    def take(self):
        """ Take the next token """
        if not self._nxt:
            nxt = next(self._nxt_func, Token.EOF)
            self._nxt.append(nxt)
        return self._nxt.pop(0)


class Token(enum.Enum):
    LPAR = 1
    RPAR = 2
    EOF = 3
