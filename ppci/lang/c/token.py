import enum
from ..common import Token


class CToken(Token):
    """ C token (including optional preceeding spaces) """
    def __init__(self, typ, val, space, first, loc):
        super().__init__(typ, val, loc)
        self.space = space
        self.first = first

    def __repr__(self):
        return 'CToken({}, {}, {}, "{}", {})'.format(
            self.typ, self.val, self.first, self.space, self.loc)

    def __str__(self):
        return self.space + self.val

    def copy(self, space=None, first=None):
        """ Return a new token which is a mildly modified copy """
        if space is None:
            space = self.space
        if first is None:
            first = self.first
        return CToken(self.typ, self.val, space, first, self.loc)


class TokenType(enum.Enum):
    OPEN_BRACK = '['
    CLOSE_BRACK = ']'
    DOT = '.'
    COMMA = ','
    ARROW = '->'
