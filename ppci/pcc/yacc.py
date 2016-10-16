"""
  Parser generator script
"""

import types
import io
import datetime
import logging

from .baselex import BaseLexer
from ..common import Token, SourceLocation
from .grammar import Grammar
from .lr import LrParserBuilder


class XaccLexer(BaseLexer):
    def __init__(self):
        tok_spec = [
            ('ID', r'[A-Za-z][A-Za-z\d_]*', lambda typ, val: (typ, val)),
            ('STRING', r"'[^']*'", lambda typ, val: ('ID', val[1:-1])),
            ('BRACEDCODE', r'\{[^\}]*\}', lambda typ, val: (typ, val)),
            ('OTHER', r'[:;\|]', lambda typ, val: (val, val)),
            ('SKIP', r'[ ]', None)
            ]
        super().__init__(tok_spec)

    def tokenize(self, txt):
        self.line = 1
        lines = txt.split('\n')
        section = 0
        for line in lines:
            line = line.strip()
            loc = SourceLocation(self.filename, 0, 0, 0)
            if not line:
                continue  # Skip empty lines
            if line == '%%':
                section += 1
                yield Token('%%', '%%', loc)
                continue
            if section == 0:
                if line.startswith('%tokens'):
                    yield Token('%tokens', '%tokens', loc)
                    for tk in super().tokenize(line[7:], eof=False):
                        yield tk
                else:
                    yield Token('HEADER', line, loc)
            elif section == 1:
                for tk in super().tokenize(line, eof=False):
                    yield tk


class ParseError(Exception):
    pass


class XaccParser:
    """ Implements a recursive descent parser to parse grammar rules.
        We could have made an generated parser, but that would yield a chicken
        egg issue.
    """
    def __init__(self):
        pass

    def prepare_peak(self, lexer):
        self.lexer = lexer
        self.look_ahead = self.lexer.next_token()

    @property
    def Peak(self):
        """ Sneak peak to the next token in line """
        return self.look_ahead.typ

    def next_token(self):
        """ Take the next token """
        token = self.look_ahead
        self.look_ahead = self.lexer.next_token()
        return token

    def consume(self, typ):
        """ Eat next token of type typ or raise an exception """
        if self.Peak == typ:
            return self.next_token()
        else:
            raise ParseError('Expected {}, but got {}'.format(typ, self.Peak))

    def has_consumed(self, typ):
        """ Consume typ if possible and return true if so """
        if self.Peak == typ:
            self.consume(typ)
            return True
        return False

    def parse_grammar(self, lexer):
        """ Entry parse function into recursive descent parser """
        self.prepare_peak(lexer)
        # parse header
        self.headers = []
        terminals = []
        while self.Peak in ['HEADER', '%tokens']:
            if self.Peak == '%tokens':
                self.consume('%tokens')
                while self.Peak == 'ID':
                    terminals.append(self.consume('ID').val)
            else:
                self.headers.append(self.consume('HEADER').val)
        self.consume('%%')
        self.grammar = Grammar()
        self.grammar.add_terminals(terminals)
        while self.Peak != 'EOF':
            self.parse_rule()
        return self.grammar

    def parse_symbol(self):
        return self.consume('ID').val

    def parse_rhs(self):
        """ Parse the right hand side of a rule definition """
        symbols = []
        while self.Peak not in [';', 'BRACEDCODE', '|']:
            symbols.append(self.parse_symbol())
        if self.Peak == 'BRACEDCODE':
            action = self.consume('BRACEDCODE').val
            action = action[1:-1].strip()
        else:
            action = None
        return symbols, action

    def parse_rule(self):
        """ Parse a rule definition """
        p = self.parse_symbol()
        self.consume(':')
        symbols, action = self.parse_rhs()
        self.grammar.add_production(p, symbols, action)
        while self.has_consumed('|'):
            symbols, action = self.parse_rhs()
            self.grammar.add_production(p, symbols, action)
        self.consume(';')


class XaccGenerator:
    """ Generator that writes generated parser to file """
    def __init__(self):
        self.logger = logging.getLogger('yacc')

    def generate(self, grammar, headers, output_file):
        self.output_file = output_file
        self.grammar = grammar
        self.headers = headers
        self.logger.debug('Generating parser for {}'.format(grammar))
        pb = LrParserBuilder(grammar)
        self.action_table, self.goto_table = pb.generate_tables()
        self.generate_python_script()

    def print(self, *args):
        """ Print helper function that prints to output file """
        print(*args, file=self.output_file)

    def generate_python_script(self):
        """ Generate python script with the parser table """
        self.print('#!/usr/bin/python')
        stamp = datetime.datetime.now().ctime()
        self.print('""" Automatically generated on {} """'.format(stamp))
        self.print('from ppci.pcc.grammar import Production, Grammar')
        self.print('from ppci.pcc.lr import LrParser, Reduce, Shift, Accept')
        self.print('from ppci.common import Token')
        self.print('')
        for h in self.headers:
            self.print(h)
        self.print('')
        self.print('class Parser(LrParser):')
        self.print('    def __init__(self):')
        # Generate rules:
        self.print('        grammar = Grammar()')
        self.print('        grammar.add_terminals({})'.format(
            self.grammar.terminals))
        self.print('        grammar.start_symbol = "{}"'.format(
            self.grammar.start_symbol))
        for rule_number, rule in enumerate(self.grammar.productions):
            rule.f_name = 'action_{}_{}'.format(rule.name, rule_number)
            self.print(
                '        grammar.add_production("{}", {}, self.{})'
                .format(rule.name, rule.symbols, rule.f_name))
        # Fill action table:
        self.print('        action_table = {}')
        for state in self.action_table:
            action = self.action_table[state]
            self.print('        action_table[{}] = {}'.format(state, action))
        self.print('')

        # Fill goto table:
        self.print('        goto_table = {}')
        for state_number in self.goto_table:
            to = self.goto_table[state_number]
            self.print('        goto_table[{}] = {}'.format(state_number, to))
        self.print('')
        self.print(
            '        super().__init__(grammar, action_table, goto_table)')
        self.print('')

        # Generate a function for each action:
        for rule in self.grammar.productions:
            num_symbols = len(rule.symbols)
            if num_symbols > 0:
                arg_names = ['arg{}'.format(n + 1) for n in range(num_symbols)]
                args = ', '.join(arg_names)
                self.print('    def {}(self, {}):'.format(rule.f_name, args))
            else:
                self.print('    def {}(self):'.format(rule.f_name))

            self.print('        res = None')
            if rule.f is None:
                semantics = 'pass'
            elif type(rule.f) is str:
                semantics = str(rule.f)
                if semantics.strip() == '':
                    semantics = 'pass'
            else:
                raise NotImplementedError()
            for n in range(num_symbols):
                semantics = semantics.replace(
                    '${}'.format(n + 1), 'arg{}'.format(n + 1))
            # semantics = semantics.replace('$$', 'res')
            self.print('        {}'.format(semantics))
            self.print('        return res')
            self.print('')


def transform(f_in, f_out):
    src = f_in.read()
    f_in.close()

    # Construction of generator parts:
    lexer = XaccLexer()
    parser = XaccParser()
    generator = XaccGenerator()

    # Sequence source through the generator parts:
    lexer.feed(src)
    grammar = parser.parse_grammar(lexer)
    generator.generate(grammar, parser.headers, f_out)


def load_as_module(filename):
    """ Load a parser spec file, generate LR tables and create module """
    ob = io.StringIO()
    if hasattr(filename, 'read'):
        transform(filename, ob)
    else:
        transform(open(filename), ob)

    parser_mod = types.ModuleType('generated_parser')
    exec(ob.getvalue(), parser_mod.__dict__)
    return parser_mod
