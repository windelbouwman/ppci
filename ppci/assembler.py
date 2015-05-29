
import re
from .pyyacc import Grammar, EPS, EOF
from .baselex import BaseLexer
from .common import make_num
from .target.target import Target, Label, Alignment
from .target.isa import InstructionProperty, Syntax

id_regex = r'[A-Za-z_][A-Za-z\d_]*'
id_matcher = re.compile(id_regex)


class AsmLexer(BaseLexer):
    """ Lexer capable of lexing a single line """
    def __init__(self, kws=()):
        tok_spec = [
            ('REAL', r'\d+\.\d+', lambda typ, val: (typ, float(val))),
            ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
            ('NUMBER', r'\d+', self.handle_number),
            ('ID', id_regex, self.handle_id),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', r':=|[\.,=:\-+*\[\]/\(\)#@]|>=|<=|<>|>|<|}|{',
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
        val = make_num(val)
        typ = 'NUMBER'
        return typ, val


class AsmParser:
    """ Base parser for assembler language """
    def __init__(self):
        # Construct a parser given a grammar:
        tokens2 = ['ID', 'NUMBER', ',', '[', ']', ':', '+', '-', '*', '=',
                   EPS, 'COMMENT', '{', '}', '#', '@', '(', ')', EOF]
        self.g = Grammar(tokens2)

        # Global structure of assembly line:
        self.g.add_production('asmline', ['asmline2'])
        self.g.add_production('asmline', ['asmline2', 'COMMENT'])
        self.g.add_production('asmline2', ['label', 'instruction'])
        self.g.add_production('asmline2', ['instruction'])
        self.g.add_production('asmline2', ['label'])
        self.g.add_production('asmline2', [])
        self.g.start_symbol = 'asmline'

    def parse(self, lexer):
        """ Entry function to parser """
        if not hasattr(self, 'p'):
            print(self.g)
            self.p = self.g.generate_parser()
        self.p.parse(lexer)


class BaseAssembler:
    """ Assembler base class, inherited by assemblers specific for a target """
    def __init__(self, target):
        assert isinstance(target, Target)
        self.target = target
        self.inMacro = False
        self.parser = AsmParser()
        self.lexer = AsmLexer()
        self.typ2nt = {}

        # Register basic types:
        self.typ2nt[int] = 'imm'
        self.typ2nt[str] = 'str'
        self.add_rule('str', ['ID'], lambda rhs: rhs[0].val)
        self.add_rule('imm', ['NUMBER'], lambda rhs: rhs[0].val)

        # Common parser rules:
        # num = register_argument('amount',
        self.add_instruction(['align', 'imm'], lambda rhs: Alignment(rhs[1]))
        self.add_instruction(['repeat', 'imm'], self.p_repeat)
        self.add_instruction(['endrepeat'], self.p_endrepeat)
        self.add_instruction(['section', 'str'], self.p_section)
        self.add_rule('label', ['str', ':'], self.p_label)

    def add_keyword(self, keyword):
        """ Add a keyword to the grammar """
        if keyword not in self.lexer.kws:
            self.parser.g.add_terminal(keyword)
            self.lexer.add_keyword(keyword)

            # Add a rule that allows keywords to be used as identifiers
            # Since there are a lot of short mnemonic, the chance that someone
            # will use a keyword as a label, is large.
            if id_matcher.match(keyword):
                self.add_rule('str', [keyword], lambda rhs: keyword)

    def add_instruction(self, rhs, f):
        """ Add an instruction to the grammar """
        rhs2, _ = self.make_str_rhs(rhs)
        self.add_rule('instruction', rhs2, f)

    def add_rule(self, lhs, rhs, f):
        """ Helper function to add a rule, why this is required? """
        print(lhs, rhs)
        if lhs == 'instruction':
            def f_wrap(*args):
                i = f(args)
                if i:
                    self.emit(i)
        else:
            def f_wrap(*args):
                return f(args)
        self.parser.g.add_production(lhs, rhs, f_wrap)

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
                # rhs2.append('ID')
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
        rhs, arg_idx = self.make_str_rhs(ins_cls.syntax)

        def f(args):
            usable = [args[ix] for ix, _ in arg_idx]
            return ins_cls(*usable)
        self.add_instruction(rhs, f)

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
                x = cls()

            if stx.set_props:
                # Apply other rules:
                for prop, val in stx.set_props.items():
                    setattr(x, prop._name, val)

            # Set from parameters in syntax:
            for idx, prop in prop_list:
                setattr(x, prop._name, args[idx])

            return x
        self.add_rule(nt, rhs2, cs)

    def get_parameter_nt(self, arg_cls):
        """ Get parameter non terminal """
        # Lookup in map:
        if arg_cls in self.typ2nt:
            return self.typ2nt[arg_cls]

        # arg not found, try syntaxi:
        if hasattr(arg_cls, 'syntaxi'):
            nt, rules = arg_cls.syntaxi

            # Store nt for later:
            self.typ2nt[arg_cls] = nt

            # Add rules:
            for stx in rules:
                self.make_arg_func(arg_cls, nt, stx)
            return nt

        # pragma: no cover
        raise KeyError(arg_cls)

    def gen_asm_parser(self, isa):
        """ Generate assembly rules from isa """
        # Loop over all isa instructions, extracting the syntax rules:
        for i in isa.instructions:
            if hasattr(i, 'syntax'):
                self.gen_i_rule(i)

    # End of generating functions

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
        self.stream = stream

        # Split lines on \n.
        # Strip remaining \r if present.
        for line in asmsrc.split('\n'):
            self.parse_line(line.strip())

    # Parser handlers:
    def p_repeat(self, rhs):
        self.begin_repeat(rhs[1])

    def p_endrepeat(self, rhs):
        self.end_repeat()

    def p_section(self, rhs):
        self.select_section(rhs[1])

    # Parser handlers:
    def p_label(self, rhs):
        lab = Label(rhs[0])
        self.emit(lab)

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
