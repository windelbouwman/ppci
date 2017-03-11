import os
import logging

from ...common import CompilerError
from .lexer import Lexer


class CPreProcessor:
    """ A pre-processor for C source code """
    def process_file(self, f):
        context = Context()
        context.add_include_path('/usr/include')
        context.add_include_path(
            '/usr/lib/gcc/x86_64-pc-linux-gnu/6.3.1/include/')
        return context.process(f, 'test.c')


class Expander:
    """ Per source or header file an expander class is created """
    logger = logging.getLogger('preprocessor')

    def __init__(self, context):
        self.context = context
        self.if_stack = []
        self.enabled = True

    def process(self, tokens):
        """ Process a token sequence into another token sequence.

        This function returns an iterator that must be looped over.
        """
        self.tokens = tokens
        self.next_token()
        return self.process_normal()

    def peak(self, ahead):
        assert ahead == 0
        if self.token:
            return self.token.typ

    def next_token(self):
        self.token = next(self.tokens, None)

    def consume(self, typ=None, skip_space=False):
        if skip_space:
            self.skip_space()

        if not typ:
            typ = self.token.typ

        if self.token.typ != typ:
            self.error('Expected {} but got {}'.format(typ, self.token.typ))

        t = self.token
        self.next_token()
        return t

    def error(self, msg):
        raise CompilerError(msg)

    def skip_space(self):
        while self.peak(0) == 'WS':
            self.next_token()

    def process_normal(self):
        """ Iterator of processed tokens """
        # print('go process!')
        while self.peak(0):
            # TODO: assert beginning of line?
            if self.peak(0) == '#':
                # We are inside a directive!
                # yield self.consume()
                self.consume('#')
                directive = self.consume('ID', skip_space=True).val

                if directive == 'include':
                    self.consume('WS')
                    if self.peak(0) == '<':
                        # TODO: this is a bad way of getting the filename:
                        filename = ''
                        self.consume('<')
                        while self.peak(0) != '>':
                            filename += self.consume().val
                        self.consume('>')
                        include_filename = filename
                    else:
                        include_filename = self.consume('STRING').val[1:-1]

                    for token in self.context.include(include_filename):
                        yield token
                elif directive == 'ifdef':
                    test_define = self.consume('ID', skip_space=True).val
                    condition = self.context.is_defined(test_define)
                    self.if_stack.append(IfState(condition))
                elif directive == 'ifndef':
                    test_define = self.consume('ID', skip_space=True).val
                    condition = not self.context.is_defined(test_define)
                    self.if_stack.append(IfState(condition))
                elif directive == 'endif':
                    self.if_stack.pop(-1)
                elif directive == 'define':
                    name = self.consume('ID', skip_space=True).val
                    value = self.parse_expression()
                    self.context.define(name, value)
                elif directive == 'if':
                    self.do_if()
                else:
                    self.logger.error('todo: %s', directive)
                    raise NotImplementedError(directive)

                assert self.peak(0) == 'BOL'
                # raise NotImplementedError()
            else:
                yield self.consume()

        if self.if_stack:
            raise CompilerError('#if not properly closed')

    def do_if(self):
        # v = self.consume('ID')
        pass

    def parse_expression(self):
        expr = []
        while not self.peak(0) == 'BOL':
            expr.append(self.consume())
        return expr


class IfState:
    """ If status for use on the if-stack """
    def __init__(self, condition):
        self.condition = condition


class Context:
    """ A context for preprocessing """
    logger = logging.getLogger('preprocessor')

    def __init__(self):
        self.defines = {}
        self.include_directories = []

    def add_include_path(self, path):
        self.include_directories.append(path)

    def define(self, name, value):
        self.defines[name] = value

    def undefine(self, name):
        self.defines.delete(name)

    def is_defined(self, name):
        return name in self.defines

    def process(self, f, filename):
        """ Process the given open file into current output """
        self.logger.debug('Processing %s', filename)
        clexer = Lexer()
        tokens = clexer.lex(f, filename)
        macro_expander = Expander(self)
        for token in macro_expander.process(tokens):
            yield token

    def include(self, filename):
        """ Include the given filename into the current output """
        for path in self.include_directories:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                self.logger.debug('Including %s', full_path)
                with open(full_path, 'r') as f:
                    for token in self.process(f, full_path):
                        yield token
                return
        self.logger.error('File not found: %s', filename)
        raise FileNotFoundError(filename)


class CTokenPrinter:
    """ Printer that can turn a preprocessed stream of tokens into text """
    def dump(self, tokens):
        for token in tokens:
            print(token)
            print(token.val, end='')


def prepare_for_parsing(tokens):
    """ Strip out tokens on the way from preprocessor to parser.

    Apply several modifications on the token stream to adapt it
    to the format that the parser requires.

    This involves:
    - Removal of whitespace
    """
    keywords = ['true', 'false',
                'else', 'if', 'while', 'for', 'return',
                'struct', 'enum',
                'typedef', 'static', 'const',
                'int', 'void', 'char', 'float', 'double']

    for token in tokens:
        if token.typ in ['BOL', 'WS']:
            pass
        elif token.typ == 'ID':
            if token.val in keywords:
                token.typ = token.val
            yield token
        else:
            yield token
