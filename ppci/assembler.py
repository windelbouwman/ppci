
import re
from . import pyyacc
from .baselex import BaseLexer
from . import Token, CompilerError, SourceLocation, make_num
from .target import Target, Label


def bit_type(value):
    assert value < (2**32)
    assert value >= 0
    t = 'val32'
    for n in [16, 12, 8, 5, 3]:
        if value < (2**n):
            t = 'val{}'.format(n)
    return t


class AsmLexer(BaseLexer):
    """ Lexer capable of lexing a single line """
    def __init__(self, kws):
        tok_spec = [
           ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
           ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
           ('NUMBER', r'\d+', self.handle_number),
           ('ID', r'[A-Za-z][A-Za-z\d_]*', self.handle_id),
           ('SKIP', r'[ \t]', None),
           ('LEESTEKEN', r':=|[\.,=:\-+*\[\]/\(\)]|>=|<=|<>|>|<|}|{', lambda typ, val: (val, val)),
           ('STRING', r"'.*?'", lambda typ, val: (typ, val[1:-1])),
           ('COMMENT', r";.*", None)
        ]
        super().__init__(tok_spec)
        self.kws = kws

    def handle_id(self, typ, val):
        if val.lower() in self.kws:
            typ = val.lower()
        return (typ, val)

    def handle_number(self, typ, val):
        val = make_num(val)
        typ = bit_type(val)
        return typ, val


class Parser:
    def add_rule(self, prod, rhs, f):
        """ Helper function to add a rule, why this is required? """
        if prod == 'instruction':
            def f_wrap(*args):
                i = f(args)
                if i:
                    self.emit(i)
        else:
            def f_wrap(*rhs):
                return f(rhs)
        self.g.add_production(prod, rhs, f_wrap)

    def __init__(self, kws, instruction_rules, emit):
        # Construct a parser given a grammar:
        tokens2 = ['ID', 'NUMBER', ',', '[', ']', ':', '+', '-', '*', '=',
                   pyyacc.EPS, 'COMMENT', '{', '}',
                   pyyacc.EOF, 'val32', 'val16', 'val12', 'val8', 'val5', 'val3']
        tokens2.extend(kws)
        self.kws = kws
        g = pyyacc.Grammar(tokens2)
        self.g = g
        # Global structure of assembly line:
        g.add_production('asmline', ['asmline2'])
        g.add_production('asmline', ['asmline2', 'COMMENT'])
        g.add_production('asmline2', ['label', 'instruction'])
        g.add_production('asmline2', ['instruction'])
        g.add_production('asmline2', ['label'])
        g.add_production('asmline2', [])
        g.add_production('label', ['ID', ':'], self.p_label)

        # Add instruction rules for the target in question:
        for prod, rhs, f in instruction_rules:
            self.add_rule(prod, rhs, f)

        #g.add_production('instruction', [])
        g.start_symbol = 'asmline'
        self.emit = emit
        self.p = g.generate_parser()
        # print('length of table:', len(self.p.action_table))

    # Parser handlers:

    def p_label(self, lname, cn):
        lab = Label(lname.val)
        self.emit(lab)

    def parse(self, lexer):
        self.p.parse(lexer)


class BaseAssembler:
    """ Assembler base class, inherited by assemblers specific for a target """
    def __init__(self, target):
        self.target = target
        assert isinstance(target, Target)

    def make_parser(self):
        self.parser = Parser(self.target.asm_keywords, self.target.assembler_rules, self.emit)
        self.lexer = AsmLexer(self.target.asm_keywords)

    def prepare(self):
        pass

    def emit(self, *args):
        self.stream.emit(*args)

    # Top level interface:
    def parse_line(self, line):
        """ Parse line into assembly instructions """
        self.lexer.feed(line)
        self.parser.parse(self.lexer)

    def assemble(self, asmsrc, stream):
        """ Assemble this source snippet """
        if type(asmsrc) is str:
            pass
        elif hasattr(asmsrc, 'read'):
            asmsrc2 = asmsrc.read()
            asmsrc.close()
            asmsrc = asmsrc2
        # TODO: use generic newline??
        # TODO: the bothersome newline ...
        self.stream = stream
        for line in asmsrc.split('\n'):
            self.parse_line(line)

    def flush(self):
        pass
