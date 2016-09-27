"""
    This module contains the generic assembly language processor. The
    Assembler class can be created and provided with one or more isa's.
    These can then be assembled.
"""

import re
from ..pcc.grammar import Grammar
from ..pcc.earley import EarleyParser
from ..pcc.baselex import BaseLexer, EPS, EOF
from ..common import make_num
from ..arch.arch import Label, Alignment, SectionInstruction, DebugData
from ..arch.encoding import Operand, Syntax, Register
from ..common import CompilerError, SourceLocation
from .debuginfo import DebugLocation, DebugDb

id_regex = r'[A-Za-z_][A-Za-z\d_]*'
id_matcher = re.compile(id_regex)


class AsmLexer(BaseLexer):
    """ Lexer capable of lexing a single line """
    def __init__(self, kws=()):
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('BINNUMBER', r'(0b|%)[0-1]+', self.handle_number),
            ('HEXNUMBER', r'(0x|\$)[0-9a-fA-F]+', self.handle_number),
            ('NUMBER', r'\d+', self.handle_number),
            ('ID', id_regex, self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('GLYPH', '|'.join(re.escape(c) for c in Syntax.GLYPHS),
                lambda typ, val: (val, val)),
            ('STRING', r"'.*?'", lambda typ, val: (typ, val[1:-1])),
            ('COMMENT', r";.*", None)
        ]
        super().__init__(tok_spec)
        self.kws = set(kws)

    def handle_id(self, typ, val):
        if val.lower() in self.kws:
            typ = val.lower()
        return typ, val

    def add_keyword(self, keyword):
        """ Add a keyword """
        self.kws.add(keyword)

    def handle_number(self, typ, val):
        """ Handle a number during lexing """
        val = make_num(val)
        typ = 'NUMBER'
        return typ, val


class AsmParser:
    """ Base parser for assembler language """
    def __init__(self):
        # Construct a parser given a grammar:
        terminals = ['ID', 'NUMBER', EPS, 'COMMENT', EOF] + Syntax.GLYPHS
        self.g = Grammar()
        self.g.add_terminals(terminals)

        # Global structure of assembly line:
        self.g.add_production('asmline', ['asmline2'])
        # self.g.add_production('asmline', ['asmline2', 'COMMENT'])
        self.g.add_production(
            'asmline2',
            ['$str$', ':', 'instruction'], self.handle_label_ins)
        self.g.add_production('asmline2', ['instruction'], self.handle_ins)
        self.g.add_production('asmline2', ['$str$', ':'], self.handle_label)
        self.g.add_production('asmline2', ['directive'])
        self.g.add_production('asmline2', [])
        self.g.start_symbol = 'asmline'

    def handle_ins(self, i):
        # if i:
        self.emit(i)

    def handle_label(self, i1, _):
        self.emit(Label(i1))

    def handle_label_ins(self, i1, _, i2):
        self.emit(Label(i1))
        if i2:
            self.emit(i2)

    def parse(self, lexer):
        """ Entry function to parser """
        if not hasattr(self, 'p'):
            self.p = EarleyParser(self.g)
        self.p.parse(lexer)


class BaseAssembler:
    """ Assembler base class, inherited by assemblers specific for a target """
    str_id = '$str$'
    int_id = '$int$'

    def __init__(self):
        self.in_macro = False
        self.stream = None
        self.parser = AsmParser()
        self.parser.emit = self.emit
        self.lexer = AsmLexer()
        self.typ2nt = {}

        # Register basic types:
        self.typ2nt[int] = self.int_id
        self.typ2nt[str] = self.str_id
        self.add_rule(self.str_id, ['ID'], lambda rhs: rhs[0].val)
        self.add_rule(self.int_id, ['NUMBER'], lambda rhs: rhs[0].val)
        self.add_rule(self.int_id, ['-', 'NUMBER'], lambda rhs: -rhs[1].val)

        # Common parser rules:
        # num = register_argument('amount',
        self.add_instruction(
            ['align', self.int_id], lambda rhs: Alignment(rhs[1]))
        self.add_instruction(
            ['section', self.str_id], lambda rhs: SectionInstruction(rhs[1]))
        self.add_rule('directive', ['repeat', self.int_id], self.p_repeat)
        self.add_rule('directive', ['endrepeat'], self.p_endrepeat)
        self.add_keyword('repeat')
        self.add_keyword('endrepeat')

    def add_keyword(self, keyword):
        """ Add a keyword to the grammar """
        if keyword not in self.lexer.kws:
            self.parser.g.add_terminal(keyword)
            self.lexer.add_keyword(keyword)

            # Add a rule that allows keywords to be used as identifiers
            # Since there are a lot of short mnemonic, the chance that someone
            # will use a keyword as a label, is large.
            if id_matcher.match(keyword):
                self.add_rule(self.str_id, [keyword], lambda rhs: keyword)

    def add_instruction(self, rhs, f, priority=0):
        """ Add an instruction to the grammar """
        rhs2 = self.resolve_rhs(rhs)
        self.add_rule('instruction', rhs2, f, priority=priority)

    def add_rule(self, lhs, rhs, f, priority=0):
        """ Helper function to add a rule, why this is required? """
        def f_wrap(*args):
            return f(args)
        self.parser.g.add_production(lhs, rhs, f_wrap, priority=priority)

    # Functions to automate the adding of instructions to asm syntax:
    def gen_asm_parser(self, isa):
        """ Generate assembly rules from isa """
        # Generate rules for instructions that have a syntax:
        for instruction in isa.instructions:
            if instruction.syntax:
                self.generate_syntax_rule(
                    instruction, 'instruction', instruction.syntax)
        # self.parser.g.dump()

    def generate_syntax_rule(self, cls, nt, stx):
        """ Construct a rule for rhs <- nt
            Take the syntax, lookup properties to strings.
            Construct a sequence of only strings
            Create a function that maps the correct properties to
            the newly created class.
            Apply other properties.
        """
        assert isinstance(stx, Syntax)

        rhs = self.resolve_rhs(stx.get_args())

        prop_list = []
        for idx, rhs_part in enumerate(stx.get_args()):
            if isinstance(rhs_part, Operand):
                prop_list.append(idx)

        def cs(args):
            # Create new class:
            usable = [args[idx] for idx in prop_list]
            return cls(*usable)
        self.add_rule(nt, rhs, cs, stx.priority)

    def resolve_rhs(self, rhs):
        """ Determine what parts of rhs are non-string and resolve """
        resolved_rhs = []
        for rhs_part in rhs:
            if isinstance(rhs_part, str):
                resolved_rhs.append(rhs_part)

                # Check if string is registered, if not, we have a new keyword
                # TODO: this is potentially error prone..
                if rhs_part not in self.parser.g.nonterminals:
                    self.add_keyword(rhs_part)
            elif isinstance(rhs_part, Operand):
                resolved_rhs.append(self.get_parameter_nt(rhs_part._cls))
            else:  # pragma: no cover
                raise NotImplementedError(str(rhs_part))
        return resolved_rhs

    def get_parameter_nt(self, arg_cls):
        """ Get parameter non terminal """
        # Lookup in map:
        if arg_cls in self.typ2nt:
            return self.typ2nt[arg_cls]

        if isinstance(arg_cls, tuple):
            assert len(arg_cls) > 0
            nt = 'w00t{}'.format(id(arg_cls))
            assert nt not in self.typ2nt.values()
            self.typ2nt[arg_cls] = nt
            for con in arg_cls:
                self.generate_syntax_rule(con, nt, con.syntax)
            # raise NotImplementedError()
            return nt
        else:
            # arg not found, try syntaxi:
            # This means, find all subclasses of this composite type, and use
            # these syntaxes.
            assert issubclass(arg_cls, Register)
            # TODO: figure a nice way for this:

            # create a non-terminal name:
            nt = '$reg_cls_{}$'.format(arg_cls.__name__.lower())

            # Store nt for later:
            self.typ2nt[arg_cls] = nt

            # Add rules for each register:
            for register in arg_cls.all_registers():
                assert isinstance(register, arg_cls)
                self.make_register_rule_function(nt, register)
            return nt

    def make_register_rule_function(self, nt, register):
        """ Create a function that can be used for a register grammar rule """
        def cs(_):
            return register
        rhs = self.resolve_rhs(self.split_text(register.name))
        self.add_rule(nt, rhs, cs)
        for aka in register.aka:
            rhs = self.resolve_rhs(self.split_text(aka))
            self.add_rule(nt, rhs, cs)

    def split_text(self, txt):
        """ Split text into lexical tokens """
        return [t.val for t in self.lexer.tokenize(txt.lower())]

    # End of generating functions

    def prepare(self):
        self.in_macro = False

    def emit(self, instruction):
        if self.in_macro:
            self.recording.append(instruction)
        else:
            self.stream.emit(instruction)

    # Top level interface:
    def parse_line(self, line):
        """ Parse line into assembly instructions """
        try:
            self.lexer.feed(line)
            self.parser.parse(self.lexer)
        except CompilerError:
            loc = SourceLocation(self.filename, self.line_no, 1, 0)
            raise CompilerError('Unable to assemble: {}'.format(line), loc)

    def assemble(self, asmsrc, stream, diag, debug=False):
        """ Assemble the source snippet into the given output stream """
        self.stream = stream

        self.filename = None
        if isinstance(asmsrc, str):
            pass
        elif hasattr(asmsrc, 'read'):
            if hasattr(asmsrc, 'name'):
                self.filename = asmsrc.name
            asmsrc2 = asmsrc.read()
            asmsrc.close()
            asmsrc = asmsrc2

        if self.filename:
            diag.add_source(self.filename, asmsrc)

        # Split lines on \n.
        # Strip remaining \r if present.
        self.line_no = 0
        debug_data = []
        debug_db = DebugDb()
        for line in asmsrc.split('\n'):
            if debug and self.filename:
                loc = SourceLocation(self.filename, self.line_no, 1, 1)
                label_name = debug_db.new_label()
                self.emit(Label(label_name))
                d = DebugLocation(loc, address=label_name)
                debug_data.append(DebugData(d))
            self.line_no += 1
            self.parse_line(line.strip())

        # Emit debug info:
        for d in debug_data:
            stream.emit(d)

    # Parser handlers:
    def p_repeat(self, rhs):
        self.begin_repeat(rhs[1])

    def p_endrepeat(self, rhs):
        self.end_repeat()

    # Parser handlers:
    def flush(self):
        pass

    # Macro language handlers:
    def begin_repeat(self, count):
        """ Handle begin of repeat macro """
        assert not self.in_macro
        self.in_macro = True
        self.rep_count = count
        self.recording = []

    def end_repeat(self):
        assert self.in_macro
        self.in_macro = False
        for rec in self.recording * self.rep_count:
            self.emit(rec)
