import os
import logging

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

    def process(self, tokens):
        """ Process a token sequence into another token sequence.

        This function returns an iterator that must be looped over.
        """
        self.tokens = tokens
        self.t = next(tokens, None)
        return self.process_normal()

    def peak(self, ahead):
        assert ahead == 0
        if self.t:
            return self.t.typ

    def consume(self, typ=None, skip_space=True):
        if not typ:
            typ = self.t.typ
        assert self.t.typ == typ
        t = self.t
        self.t = next(self.tokens, None)
        # print(t)
        return t

    def process_normal(self):
        """ Iterator of processed tokens """
        # print('go process!')
        while self.peak(0):
            if self.peak(0) == '#':
                # We are inside a directive!
                # yield self.consume()
                self.consume()
                # assert self.peak(0) == 'ID'
                if self.peak(0) == 'WS':
                    self.consume()

                directive = self.consume().val

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
                elif directive == 'ifndef':
                    self.consume('WS')
                    test_define = self.consume('ID')
                elif directive == 'define':
                    name = get_token()
                    self.context.define(name, value)
                elif directive == '#ifdef':
                    self.do_ifdef()
                elif directive == '#ifdef':
                    pass
                else:
                    self.logger.error('todo: %s', directive)
                    raise NotImplementedError(directive)

                assert self.peak(0) == 'BOL'
                # raise NotImplementedError()
            else:
                yield self.consume()

    def do_ifdef(self):
        while not '#endif':
            yield 2


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

    def process(self, f, filename):
        """ Process the given open file into current output """
        self.logger.debug('Processing %s', filename)
        l = Lexer()
        tokens = l.lex(f, filename)
        x = Expander(self)
        for token in x.process(tokens):
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
            print(token.val, end='')


def prepare_for_parsing(tokens):
    """ Strip out tokens on the way from preprocessor to parser """
    for token in tokens:
        if token.typ in ['BOL', 'WS']:
            pass
        else:
            print('Bridge', token)
            yield token
