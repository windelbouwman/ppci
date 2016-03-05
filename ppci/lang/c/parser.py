from .lexer import Lexer


class Parser:
    """ C Parser """
    def __init__(self):
        self.lexer = Lexer()

    def parse(self, src):
        self.lexer.lex(src)
        return
