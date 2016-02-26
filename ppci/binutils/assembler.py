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
from ..arch.arch import Label, Alignment
from ..arch.isa import InstructionProperty, Syntax
from ..common import CompilerError, SourceLocation

id_regex = r'[A-Za-z_][A-Za-z\d_\.]*'
id_matcher = re.compile(id_regex)


class AsmLexer(BaseLexer):
    """ Lexer capable of lexing a single line """
    def __init__(self, kws=()):
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
            ('NUMBER', r'\d+', self.handle_number),
            ('LABEL', id_regex + ':', lambda typ, val: (typ, val)),
            ('ID', id_regex, self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', r':=|[,=:\-+*\[\]/\(\)#@\&]|>=|<=|<>|>|<|}|{',
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
        terminals = ['ID', 'NUMBER', ',', '[', ']', ':', '+', '-', '*', '=',
                     EPS, 'COMMENT', '{', '}', '#', '@', '(', ')', EOF]
        self.g = Grammar()
        self.g.add_terminals(terminals)

        # Global structure of assembly line:
        self.g.add_production('asmline', ['asmline2'])
        self.g.add_production('asmline', ['asmline2', 'COMMENT'])
        self.g.add_production(
            'asmline2',
            ['LABEL', 'instruction'], self.handle_label_ins)
        self.g.add_production('asmline2', ['instruction'], self.handle_ins)
        self.g.add_production('asmline2', ['LABEL'], self.handle_label)
        self.g.add_production('asmline2', ['directive'])
        self.g.add_production('asmline2', [])
        self.g.start_symbol = 'asmline'

    def handle_ins(self, i):
        if i:
            self.emit(i)

    def handle_label(self, i1):
        self.emit(Label(i1.val[:-1]))

    def handle_label_ins(self, i1, i2):
        self.emit(Label(i1.val[:-1]))
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
        self.add_rule('directive', ['repeat', self.int_id], self.p_repeat)
        self.add_rule('directive', ['endrepeat'], self.p_endrepeat)
        self.add_rule('directive', ['section', self.str_id], self.p_section)
        self.add_keyword('repeat')
        self.add_keyword('endrepeat')
        self.add_keyword('section')

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
        rhs2, _ = self.make_str_rhs(rhs)
        self.add_rule('instruction', rhs2, f, priority=priority)

    def add_rule(self, lhs, rhs, f, priority=0):
        """ Helper function to add a rule, why this is required? """
        def f_wrap(*args):
            return f(args)
        self.parser.g.add_production(lhs, rhs, f_wrap, priority=priority)

    # Functions to automate the adding of instructions to asm syntax:
    def make_str_rhs(self, rhs):
        """ Determine what parts of rhs are non-string and resolve """
        rhs2 = []
        prop_list = []
        for idx, rhs_part in enumerate(rhs):
            if type(rhs_part) is str:
                rhs2.append(rhs_part)

                # Check if string is registered, if not, we have a new keyword
                # TODO: this is potentially error prone..
                if rhs_part not in self.parser.g.nonterminals:
                    self.add_keyword(rhs_part)
            elif type(rhs_part) is InstructionProperty:
                arg_cls = rhs_part._cls
                rhs2.append(self.get_parameter_nt(arg_cls))
                prop_list.append((idx, rhs_part))
            else:  # pragma: no cover
                raise NotImplementedError(str(rhs_part))
        return rhs2, prop_list

    def gen_i_rule(self, ins_cls):
        """ Generate rule ... """
        # We must use function call here, otherwise the closure does not work..
        rhs, arg_idx = self.make_str_rhs(ins_cls.syntax.syntax)

        def f(args):
            usable = [args[ix] for ix, _ in arg_idx]
            return ins_cls(*usable)
        self.add_instruction(rhs, f, priority=ins_cls.syntax.priority)

    def make_arg_func(self, cls, nt, stx):
        """ Construct a rule for rhs <- nt
            Take the syntax, lookup properties to strings.
            Construct a sequence of only strings
            Create a function that maps the correct properties to
            the newly created class.
            Apply other properties.
        """
        assert isinstance(stx, Syntax)

        rhs2, prop_list = self.make_str_rhs(stx.syntax)

        def cs(args):
            # Create new class:
            if stx.new_func:
                # Use a function to create the class:
                x = stx.new_func()
            else:
                usable = [args[ix] for ix, _ in prop_list]
                x = cls(*usable)

            return x
        self.add_rule(nt, rhs2, cs, stx.priority)

    def get_parameter_nt(self, arg_cls):
        """ Get parameter non terminal """
        # Lookup in map:
        if arg_cls in self.typ2nt:
            return self.typ2nt[arg_cls]

        # arg not found, try syntaxi:
        # This means, find all subclasses of this composite type, and use
        # these syntaxes.
        if hasattr(arg_cls, 'syntaxi'):
            syntaxi = arg_cls.syntaxi
            # TODO: figure a nice way for this:
            if isinstance(syntaxi, tuple):
                # In case of a tuple, the options are not subclasses, but
                # listed in the tuple:
                nt, rules = arg_cls.syntaxi

                # Store nt for later:
                self.typ2nt[arg_cls] = nt

                # Add rules:
                for stx in rules:
                    self.make_arg_func(arg_cls, nt, stx)
                return nt
            else:
                nt = arg_cls.syntaxi

                # Store nt for later:
                self.typ2nt[arg_cls] = nt

                # Add rules:
                for subcon in arg_cls.__subclasses__():
                    self.make_arg_func(subcon, nt, subcon.syntax)
                return nt

        raise KeyError(arg_cls)  # pragma: no cover

    def gen_asm_parser(self, isa):
        """ Generate assembly rules from isa """
        # Loop over all isa instructions, extracting the syntax rules:
        instructions = [i for i in isa.instructions if i.syntax]

        # Generate rules for instructions:
        for ins in instructions:
            self.gen_i_rule(ins)

    # End of generating functions

    def prepare(self):
        self.in_macro = False

    def emit(self, *args):
        if self.in_macro:
            self.recording.append(args)
        else:
            self.stream.emit(*args)

    # Top level interface:
    def parse_line(self, line):
        """ Parse line into assembly instructions """
        try:
            self.lexer.feed(line)
            self.parser.parse(self.lexer)
        except CompilerError:
            loc = SourceLocation(self.filename, self.line_no, 1, 0)
            raise CompilerError('Unable to assemble: {}'.format(line), loc)

    def assemble(self, asmsrc, stream, diag):
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
        for line in asmsrc.split('\n'):
            self.line_no += 1
            self.parse_line(line.strip())

    # Parser handlers:
    def p_repeat(self, rhs):
        self.begin_repeat(rhs[1])

    def p_endrepeat(self, rhs):
        self.end_repeat()

    def p_section(self, rhs):
        self.select_section(rhs[1])

    # Parser handlers:
    def select_section(self, name):
        """ Switch to another section section in the instruction stream """
        self.flush()
        self.stream.select_section(name)

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
            self.emit(*rec)
