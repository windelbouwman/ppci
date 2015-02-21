
from . import pyyacc
from .baselex import BaseLexer
from .common import make_num
from .target import Target, Label
from .target.basetarget import Alignment


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
    def __init__(self, kws=()):
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
            ('NUMBER', r'\d+', self.handle_number),
            ('ID', r'[A-Za-z][A-Za-z\d_]*', self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', r':=|[\.,=:\-+*\[\]/\(\)]|>=|<=|<>|>|<|}|{',
                lambda typ, val: (val, val)),
            ('STRING', r"'.*?'", lambda typ, val: (typ, val[1:-1])),
            ('COMMENT', r";.*", None)
        ]
        super().__init__(tok_spec)
        self.kws = set(kws)

    def handle_id(self, typ, val):
        if val.lower() in self.kws:
            typ = val.lower()
        return (typ, val)

    def add_keyword(self, keyword):
        """ Add a keyword """
        self.kws.add(keyword)

    def handle_number(self, typ, val):
        val = make_num(val)
        typ = bit_type(val)
        return typ, val


class AsmParser:
    """ Base parser for assembler language """
    def __init__(self, emit):
        # Construct a parser given a grammar:
        tokens2 = ['ID', 'NUMBER', ',', '[', ']', ':', '+', '-', '*', '=',
                   pyyacc.EPS, 'COMMENT', '{', '}',
                   pyyacc.EOF,
                   'val32', 'val16', 'val12', 'val8', 'val5', 'val3']
        g = pyyacc.Grammar(tokens2)
        self.g = g

        # Global structure of assembly line:
        g.add_production('asmline', ['asmline2'])
        g.add_production('asmline', ['asmline2', 'COMMENT'])
        g.add_production('asmline2', ['label', 'instruction'])
        g.add_production('asmline2', ['instruction'])
        g.add_production('asmline2', ['label'])
        g.add_production('asmline2', [])

        # Pseudo instructions:
        g.add_production('label', ['ID', ':'], self.p_label)

        # Add handy rules:
        self.add_rule('imm32', ['val32'], lambda rhs: rhs[0].val)
        self.add_rule('imm32', ['imm16'], lambda rhs: rhs[0])
        self.add_rule('imm16', ['val16'], lambda rhs: rhs[0].val)
        self.add_rule('imm16', ['imm12'], lambda rhs: rhs[0])
        self.add_rule('imm12', ['val12'], lambda rhs: rhs[0].val)
        self.add_rule('imm12', ['imm8'], lambda rhs: rhs[0])
        self.add_rule('imm8', ['val8'], lambda rhs: rhs[0].val)
        self.add_rule('imm8', ['imm5'], lambda rhs: rhs[0])
        self.add_rule('imm5', ['val5'], lambda rhs: rhs[0].val)
        self.add_rule('imm5', ['imm3'], lambda rhs: rhs[0])
        self.add_rule('imm3', ['val3'], lambda rhs: rhs[0].val)

        g.start_symbol = 'asmline'
        self.emit = emit
        # print('length of table:', len(self.p.action_table))

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

    def add_instruction(self, rhs, f):
        self.add_rule('instruction', rhs, f)

    # Parser handlers:
    def p_label(self, lname, cn):
        lab = Label(lname.val)
        self.emit(lab)

    def parse(self, lexer):
        """ Entry function to parser """
        if not hasattr(self, 'p'):
            self.p = self.g.generate_parser()
        self.p.parse(lexer)


class BaseAssembler:
    """ Assembler base class, inherited by assemblers specific for a target """
    def __init__(self, target):
        assert isinstance(target, Target)
        self.target = target
        self.inMacro = False
        self.parser = AsmParser(self.emit)
        self.lexer = AsmLexer()

        # Common parser rules:
        self.add_keyword('repeat')
        self.add_keyword('endrepeat')
        self.add_keyword('section')
        self.add_keyword('align')
        self.add_instruction(['align', 'imm8'], lambda rhs: Alignment(rhs[1]))
        self.add_instruction(['repeat', 'imm32'], self.p_repeat)
        self.add_instruction(['endrepeat'], self.p_endrepeat)
        self.add_instruction(['section', 'ID'], self.p_section)

    def add_keyword(self, keyword):
        self.parser.g.add_terminal(keyword)
        self.lexer.add_keyword(keyword)

    def add_instruction(self, rhs, f):
        self.parser.add_instruction(rhs, f)

    def add_rule(self, lhs, rhs, f):
        self.parser.add_rule(lhs, rhs, f)

    def gen_i_rule(self, cls, arg_idx, rhs):
        # We must use function call here, otherwise the closure does not work..
        def f(*args):
            args = args[0]  # Extract tuple??
            usable = [args[ix] for ix in arg_idx]
            return cls(*usable)
        self.add_instruction(rhs, f)

    def gen_asm_parser(self, isa):
        """ Generate assembly rules from isa """
        # Loop over all isa instructions, extracting the syntax rules:
        for i in isa.instructions:
            if hasattr(i, 'syntax'):
                rhs = []
                arg_idx = []
                for idx, st in enumerate(i.syntax):
                    if type(st) is int:
                        rhs.append(isa.typ2nt[i.args[st][1]])
                        arg_idx.append(idx)
                    elif type(st) is str:
                        rhs.append(st)
                    else:
                        raise Exception()
                cls = i
                self.gen_i_rule(cls, arg_idx, rhs)

    def prepare(self):
        self.inMacro = False

    def emit(self, *args):
        if self.inMacro:
            self.recording.append(args)
        else:
            self.stream.emit(*args)

    # Top level interface:
    def parse_line(self, line):
        """ Parse line into assembly instructions """
        self.lexer.feed(line)
        self.parser.parse(self.lexer)

    def assemble(self, asmsrc, stream):
        """ Assemble the source snippet into the given output stream """
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

    # Parser handlers:
    def p_repeat(self, rhs):
        self.begin_repeat(rhs[1])

    def p_endrepeat(self, rhs):
        self.end_repeat()

    def p_section(self, rhs):
        self.select_section(rhs[1].val)

    def select_section(self, name):
        """ Switch to another section section in the instruction stream """
        self.flush()
        self.stream.select_section(name)

    def flush(self):
        pass

    # Macro language handlers:
    def begin_repeat(self, count):
        """ Handle begin of repeat macro """
        assert not self.inMacro
        self.inMacro = True
        self.rep_count = count
        self.recording = []

    def end_repeat(self):
        assert self.inMacro
        self.inMacro = False
        for rec in self.recording * self.rep_count:
            self.emit(*rec)
