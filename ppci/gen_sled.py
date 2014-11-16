
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


def pattern(*args):
    name, val = args
    p = Pattern()
    p.mapping[name] = val
    return p


def constructor(name, parts, assignment):
    c = Constructor(name)
    c.parts = parts
    c.assignment = assignment
    return c


class Token:
    def __init__(self, width):
        self.fields = []
        self.name = 'todo'


class Field:
    """ Specific bit field """
    def __init__(self, token, start, end):
        self.name = None
        self.token = token
        self.start = start
        self.end = end
        self.token.fields.append(self)

    def __repr__(self):
        return 'fld{}-{}'.format(self.start, self.end)


class Pattern:
    """ Mappings from names to values """
    def __init__(self):
        self.mapping = {}

    def __repr__(self):
        return '{} {}'.format('pat', self.mapping)

    def __or__(self, other):
        p = Pattern()
        p.mapping.update(self.mapping)
        p.mapping.update(other.mapping)
        return p

    @property
    def value(self):
        values = list(self.mapping.values())
        return values[0]

    @property
    def name(self):
        if hasattr(self, '_name'):
            return self._name
        names = list(self.mapping.keys())
        return names[0]

    @property
    def multiple(self):
        return len(self.mapping) > 1


class Assignment:
    """ Assignment of patterns to fields """
    def __init__(self):
        self.assignment_map = {}

    def __repr__(self):
        return ','.join('{}={}'.format(field, pattern) for field, pattern in self.assignment_map.items())

    def __or__(self, other):
        a = Assignment()
        a.assignment_map.update(self.assignment_map)
        a.assignment_map.update(other.assignment_map)
        return a

    @property
    def pattern(self):
        assignments = list(self.assignment_map.values())
        return assignments[0]

    @property
    def bitfield(self):
        bitfields = list(self.assignment_map.keys())
        return bitfields[0]


def assign(a, b):
    ass = Assignment()
    ass.assignment_map[a] = b
    return ass


class Constructor:
    """ Contrapt instruction form bit assignment or other constructors """
    def __init__(self, name):
        self.name = name
        self.parts = []

    def __repr__(self):
        return 'con {}'.format(self.parts)

    def __xor__(self, other):
        c = Constructor()
        for p1 in self.parts:
            if type(p1) is str:
                c.parts.append(p1)
            elif type(p1) is dict:
                for pat1 in p1.values():
                    for p2 in other.parts:
                        print('expand', pat1, p2)
            elif type(p1) is Constructor:
                c.parts.append(p1)
        print(self, other)
        return c

    @property
    def args(self):
        a = []
        for p in self.parts:
            if type(p) is Assignment:
                if p.pattern.multiple:
                    a.append(p.bitfield.name)
        return a


class Spec:
    """ Contains machine specification """
    def __init__(self):
        self.tokens = []
        self.patterns = []
        self.constructors = []

    def add_constructor(self, constructor):
        self.constructors.append(constructor)

    def add_pattern(self, lhs, rhs):
        print(lhs, rhs)

    def add_token(self, t_name):
        self.tokens.append(t_name)


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
            name = token.name
            self.print('class {}(Token):'.format(name))
            self.print('    def __init__(self):')
            self.print('        super().__init__(32)')
            for field in token.fields:
                f_name = field.name
                s = field.start
                e = field.end
                self.print('    {} = bit_range({}, {})'.format(f_name, s, e + 1))
            self.print('')

    def gen_assignment(self, a):
        for lhs, rhs in a.assignment_map.items():
            if lhs.name:
                lhs2 = lhs.name
            else:
                lhs2 = '[{}:{}]'.format(lhs.start, lhs.end)
            self.print('        self.token.{} = {}'.format(lhs2, rhs.value))

    def gen_instructions(self):
        for constructor in self.spec.constructors:
            name = constructor.name
            self.print('class {}(Instruction):'.format(name))
            self.print('    __init__(self):')
            self.print(constructor.args)
            self.print('    encode(self):')
            for a in constructor.parts:
                if type(a) is Assignment:
                    self.gen_assignment(a)
            self.gen_assignment(constructor.assignment)
            self.print('')

    def gen_parser(self):
        for constructor in self.spec.constructors:
            rhs = []
            for x in constructor.parts:
                if type(x) is str:
                    rhs.append(x)
                elif type(x) is Assignment:
                    rhs.append(x.pattern.name)
                else:
                    raise Exception()
            print(rhs)
            self.print('{}()'.format(constructor.name))

    def generate(self, spec):
        self.spec = spec
        self.print("spec generated")
        self.print('===== tokens =====')
        self.gen_tokens()
        self.print('===== instructions =====')
        self.gen_instructions()
        self.print('===== parser =====')
        self.gen_parser()
        self.print('===== done =====')


def sled_main(args):
    l = SledLexer()
    p = SledParser()
    l.feed(args.source.read())
    spec = p.parse(l)
    x = Generator()
    x.generate(spec)
