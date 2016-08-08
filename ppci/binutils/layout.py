from ..pcc.baselex import BaseLexer, EOF, EPS
from ..pcc.grammar import Grammar
from ..pcc.lr import LrParserBuilder
from ..common import make_num


class Layout:
    """ Defines a layout for the linker to be used """
    def __init__(self):
        self.memories = []

    def add_memory(self, memory):
        self.memories.append(memory)

    def __eq__(self, other):
        return self.memories == other.memories

    def __repr__(self):
        return str(self.memories)

    @staticmethod
    def load(file):
        """ Load a layout from file """
        return _lloader.load_layout(file)


class Memory:
    """ Specification of how a memory may look like and what it contains. """
    def __init__(self, name):
        self.inputs = []
        self.name = name
        self.location = 0x0
        self.size = 0x0

    def add_input(self, inp):
        assert isinstance(inp, Input)
        self.inputs.append(inp)

    def __repr__(self):
        return 'MEM {} loc={:08X} size={:08X}'.format(
            self.name, self.location, self.size) + str(self.inputs)

    def __eq__(self, other):
        return str(self) == str(other)


class Input:
    pass


class Section(Input):
    """ Insert a section here """
    def __init__(self, section_name):
        self.section_name = section_name

    def __repr__(self):
        return 'Section({})'.format(self.section_name)


class SectionData(Input):
    """ Insert only the data of a section here, not the section itself """
    def __init__(self, section_name):
        self.section_name = section_name

    def __repr__(self):
        return 'SectionData({})'.format(self.section_name)


class Align(Input):
    """ Align the current position to the given byte """
    def __init__(self, alignment):
        self.alignment = alignment

    def __repr__(self):
        return 'Align({})'.format(self.alignment)


class SymbolDefinition(Input):
    def __init__(self, symbol_name):
        self.symbol_name = symbol_name

    def __repr__(self):
        return 'Symbol define: {}'.format(self.symbol_name)


class LayoutLexer(BaseLexer):
    """ Lexer for layout files """
    kws = [
        'MEMORY', 'ALIGN', 'LOCATION', 'SECTION', 'SECTIONDATA',
        'SIZE', 'DEFINESYMBOL']

    def __init__(self):
        tok_spec = [
            ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
            ('NUMBER', r'\d+', self.handle_number),
            ('ID', r'[_A-Za-z][_A-Za-z\d_]*', self.handle_id),
            ('SKIP', r'[ \t\r\n]', None),
            ('LEESTEKEN', r':=|[\.,=:\-+*\[\]/\(\)]|>=|<=|<>|>|<|}|{',
             lambda typ, val: (val, val)),
            ('STRING', r"'.*?'", lambda typ, val: (typ, val[1:-1])),
        ]
        super().__init__(tok_spec)

    def handle_id(self, typ, val):
        if val in self.kws:
            typ = val
        return typ, val

    def handle_number(self, typ, val):
        val = make_num(val)
        typ = 'NUMBER'
        return typ, val


class LayoutParser:
    def __init__(self, kws):
        toks = [
            'ID', 'NUMBER', '{', '}', '.', ':', '=', '(', ')', EPS, EOF
            ] + kws
        grammar = Grammar()
        grammar.add_terminals(toks)
        grammar.add_production('layout', ['mem_list'])
        grammar.add_one_or_more('mem', 'mem_list')
        grammar.add_production('mem', [
            'MEMORY', 'ID', 'LOCATION', '=', 'NUMBER', 'SIZE', '=',
            'NUMBER', '{', 'input_list', '}'], self.handle_mem)
        grammar.add_one_or_more('input', 'input_list')
        grammar.add_production(
            'input', ['ALIGN', '(', 'NUMBER', ')'], self.handle_align)
        grammar.add_production(
            'input', ['SECTION', '(', 'ID', ')'], self.handle_section)
        grammar.add_production(
            'input', ['DEFINESYMBOL', '(', 'ID', ')'], self.handle_defsym)
        grammar.add_production(
            'input', ['SECTIONDATA', '(', 'ID', ')'], self.handle_section_data)

        grammar.start_symbol = 'layout'
        self.p = LrParserBuilder(grammar).generate_parser()

    def parse(self, lexer, layout):
        self.layout = layout
        self.p.parse(lexer)

    def handle_mem(self, mem_tag, mem_name, loc_tag, eq1, loc, size_tag, eq2,
                   size, lbrace, inps, rbrace):
        m = Memory(mem_name.val)
        m.size = size.val
        m.location = loc.val
        for inp in inps:
            m.add_input(inp)
        self.layout.add_memory(m)

    def handle_align(self, align_tag, lbrace, alignment, rbrace):
        return Align(alignment.val)

    def handle_section(self, section_tag, lbrace, section_name, rbrace):
        return Section(section_name.val)

    def handle_section_data(self, section_tag, lbrace, section_name, rbrace):
        return SectionData(section_name.val)

    def handle_defsym(self, section_tag, lbrace, name, rbrace):
        return SymbolDefinition(name.val)


class LayoutLoader:
    def __init__(self):
        self.lexer = LayoutLexer()
        self.parser = LayoutParser(self.lexer.kws)

    def load_layout(self, f):
        layout = Layout()

        # TODO: perhaps the read is better in the lexer?
        self.lexer.feed(f.read())
        self.parser.parse(self.lexer, layout)
        return layout


# Single definition:
_lloader = LayoutLoader()
