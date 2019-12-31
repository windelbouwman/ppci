import enum
from ..common import Token
from .utils import LineInfo


class CToken(Token):
    """ C token (including optional preceeding spaces) """

    def __init__(self, typ, val, space, first, loc):
        super().__init__(typ, val, loc)
        self.space = space
        self.first = first
        # self.hideset = set()

    def __repr__(self):
        return 'CToken({}, {}, {}, "{}", {})'.format(
            self.typ, self.val, self.first, self.space, self.loc
        )

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
    OPEN_BRACK = "["
    CLOSE_BRACK = "]"
    DOT = "."
    COMMA = ","
    ARROW = "->"


class CTokenPrinter:
    """ Printer that can turn a stream of token-lines into text """

    def dump(self, tokens, file=None):
        first_line = True
        for token in tokens:
            # print(token.typ, token.val, token.first)
            if isinstance(token, LineInfo):
                # print(token, str(token))
                print(str(token), file=file)
                first_line = True
            else:
                if token.first:
                    # Insert newline!
                    if first_line:
                        first_line = False
                    else:
                        print(file=file)
                text = str(token)
                print(text, end="", file=file)
