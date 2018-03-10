""" Functionality to tokenize and parse S-expressions.
"""

from .common import Token, SourceLocation
from ..common import CompilerError


def tokenize_sexpr(text):
    """ Generator that generates tokens for (WASM-compatible) S-expression code.
    Would need work to produce tokens suited for e.g. syntax highlighting,
    but good enough for now, to make the parser work.
    """

    comment_depth = 0
    word_start = -1
    in_string = ''
    filename = '?'

    i = -1
    while i < len(text):
        i += 1
        c = text[i:i+1]  # is '' last round so we can finish words at end of text
        next = text[i+1:i+2]
        loc = SourceLocation(filename, 1, i, 1)

        if comment_depth > 0:
            if c == '(' and next == ';':
                comment_depth += 1
                i += 1
            elif c == ';' and next == ')':
                assert comment_depth > 0
                comment_depth -= 1
                i += 1
                # if comment_depth == 0:
                #     yield ('comment', ...)
        elif in_string:
            if in_string == 2:
                in_string = 1
            elif c == '\\':
                in_string = 2
            elif c == '"':
                in_string = 0
                # drop the quotes
                yield Token('string', text[word_start+1:i], loc)
                word_start = -1
        else:
            token = None
            if c in ' \t\r\n':
                pass  # whitespace
            elif c == '(' and next == ';':
                comment_depth = 1
            elif c == ';' and next == ';':
                for j in range(i+1, len(text)):
                    if text[j] in '\r\n':
                        break
                token = Token('comment', text[i:j], loc)
                i = j
            elif c == '(':
                token = Token('bracket', '(', loc)
            elif c == ')':
                token = Token('bracket', ')', loc)
            elif c == '"':
                in_string = text[i:]
                word_start = i
                continue
            else:
                if word_start == -1:
                    word_start = i
                continue

            # Process word
            if word_start >= 0:
                word = text[word_start:i]
                word_start = -1
                if word[0] in '-+.01234567890':  # maybe a number
                    try:
                        if '.' in word or 'e' in word.lower():
                            word = float(word)
                        else:
                            word = int(word)
                    except ValueError:
                        pass
                # identifier or number or $xx thingy
                yield Token('word', word, loc)
            if token:
                yield token


tokens2ignore = ('comment', )


def parse_sexpr(text):
    """ Parse S-expression given as string.
    Returns a tuple that represents the S-expression.
    """
    assert isinstance(text, str)
    # Check start ok
    tokengen = tokenize_sexpr(text)
    for token in tokengen:
        if token.typ not in tokens2ignore:
            if token.val != '(':
                raise CompilerError(
                    'Expecting S-expression to open with "(".', token.loc)
            break
    # Parse
    result = _parse_expr(tokengen)
    # Check end ok
    more = ' '.join([str(token.val) for token in tokengen if token.typ not in tokens2ignore])
    if more:
        raise EOFError('Unexpected code after expr end: %r' % more)

    return result


def _parse_expr(tokengen):
    val = []
    for token in tokengen:
        if token.typ in tokens2ignore:
            pass
        elif token.val == '(':
            val.append(_parse_expr(tokengen))  # recurse
        elif token.val == ')':
            return tuple(val)
        else:
            val.append(token.val)
    else:
        raise EOFError('Unexpected end')
