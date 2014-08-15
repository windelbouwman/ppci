
import os
from . import pyyacc
from .baselex import BaseLexer

spec_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sled.grammar')
sled_parser = pyyacc.load_as_module(spec_file)


keywords = ['fields', 'patterns', 'constructors',
            'of', 'module', 'is', 'to']


class SledLexer(BaseLexer):
    def __init__(self):
        tok_spec = [
            ('ID', r'[A-Za-z][A-Za-z\d_]*', self.handle_id),
            ('NUMBER', r'\d+', lambda typ, val: (typ, int(val))),
            ('STRING', r"'[^']*'", lambda typ, val: ('ID', val[1:-1])),
            ('NEWLINE', r'\n', lambda typ, val: self.newline()),
            ('OTHER', r'[:;\|\]\[{}_=]', lambda typ, val: (val, val)),
            ('SKIP', r'[ ]', None)
            ]
        super().__init__(tok_spec)

    def handle_id(self, typ, val):
        if val in keywords:
            typ = val
        return typ, val


class Spec:
    def __init__(self):
        self.tokens = []
        self.patterns = []

    def add_pattern(self, lhs, rhs):
        print(lhs, rhs)

    def add_token(self, t_name, fields):
        print(t_name, fields)
        self.tokens.append((t_name, fields))


class SledParser(sled_parser.Parser):
    """ Derived from automatically generated parser """
    def parse(self, l):
        self.spec = Spec()
        super().parse(l)
        return self.spec


class Generator:
    def print(self, *args):
        print(*args)

    def gen_tokens(self):
        # Generate tokens
        for token in self.spec.tokens:
            name, fields = token
            self.print('class {}(Token):'.format(name))
            self.print('    def __init__(self):')
            self.print('        super().__init__(32)')
            self.print('')
            for field in fields:
                f_name, s, e = field
                self.print('    {} = bit_range({}, {})'.format(f_name, s, e + 1))
            self.print('')
            self.print('')
                

    def generate(self, spec):
        self.spec = spec
        self.print("spec generated")
        self.gen_tokens()


def sled_main(args):
    l = SledLexer()
    p = SledParser()
    l.feed(args.source.read())
    spec = p.parse(l)
    x = Generator()
    x.generate(spec)

