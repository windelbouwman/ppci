from .lexer import Lexer
from . import nodes


class Parser:
    """
        C Parser. implemented in a recursive descent way, like the CLANG[1]
        frontend for llvm, also without the lexer hack[2].

        [1] http://clang.org/
        [2] https://en.wikipedia.org/wiki/The_lexer_hack
    """
    def __init__(self):
        self.lexer = Lexer()

    def parse(self, src):
        """ Here the parsing of C is begun ... """
        self.tokens = self.lexer.lex(src)
        self.token = self.tokens.__next__()
        unit = self.parse_translation_unit()
        return unit

    def consume(self, typ=None):
        """ Consume a token certain type """
        if typ is None:
            typ = self.peak
        assert typ == self.peak
        return t

    def has_consumed(self, typ):
        if self.peak == typ:
            self.consume(typ)
            return True
        else:
            return False

    @property
    def peak(self):
        return self.token.typ

    def next_token(self):
        """ Advance to the next token """
        tok = self.token
        if tok.typ != 'EOF':
            self.token = self.tokens.__next__()
        return tok

    def parse_translation_unit(self):
        """ Top level begin """
        self.parse_function_definition()

    def parse_function_definition(self):
        """ Parse a function """
        pass

    def parse_statement(self):
        pass

    def parse_if_statement(self):
        """ Parse an if statement """
        self.consume('if')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        yes = self.parse_statement()
        if self.has_consumed('else'):
            no = self.parse_statement()
        else:
            no = nodes.Empty()
        return nodes.IfStatement(condition, yes, no)

    def parse_while_statement(self):
        """ Parse a while statement """
        self.consume('while')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        self.parse_statement()
        return nodes.WhileStatement(condition)

    def parse_expression(self):
        pass

    def parse_primary_expression(self):
        """ Parse a primary expression """
        pass
