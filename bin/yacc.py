#!/usr/bin/python

"""
Parser generator utility. This script can generate a python script from a
grammar description.

Invoke the script on a grammar specification file:

.. code::

    $ ./yacc.py test.x -o test_parser.py

And use the generated parser by deriving a user class:


.. code::

    import test_parser
    class MyParser(test_parser.Parser):
        pass
    p = MyParser()
    p.parse()


Alternatively you can load the parser on the fly:

.. code::

    import yacc
    parser_mod = yacc.load_as_module('mygrammar.x')
    class MyParser(parser_mod.Parser):
        pass
    p = MyParser()
    p.parse()

"""

import argparse
import re
import sys
import datetime
import types
import io
import logging
from pyyacc import Grammar
from baselex import BaseLexer
from ppci import Token, SourceLocation


class XaccLexer(BaseLexer):
    def __init__(self):
        tok_spec = [
           ('ID', r'[A-Za-z][A-Za-z\d_]*', lambda typ, val: (typ, val)),
           ('STRING', r"'[^']*'", lambda typ, val: ('ID', val[1:-1])),
           ('BRACEDCODE', r"\{[^\}]*\}", lambda typ, val: (typ, val)),
           ('OTHER', r'[:;\|]', lambda typ, val: (val, val)),
           ('SKIP', r'[ ]', None)
            ]
        super().__init__(tok_spec)

    def tokenize(self, txt):
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
                    for tk in super().tokenize(line[7:]):
                        yield tk
                else:
                    yield Token('HEADER', line, loc)
            elif section == 1:
                for tk in super().tokenize(line):
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
        self.grammar = Grammar(terminals)
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
        self.logger.info('Generating parser for grammar {}'.format(grammar))
        self.action_table, self.goto_table = grammar.generate_tables()
        self.generate_python_script()

    def print(self, *args):
        """ Print helper function that prints to output file """
        print(*args, file=self.output_file)

    def generate_python_script(self):
        """ Generate python script with the parser table """
        self.print('#!/usr/bin/python')
        stamp = datetime.datetime.now().ctime()
        self.print('""" Automatically generated by xacc on {} """'.format(stamp))
        self.print('from pyyacc import LRParser, Reduce, Shift, Accept, Production, Grammar')
        self.print('from ppci import Token')
        self.print('')
        for h in self.headers:
            print(h, file=output_file)
        self.print('')
        self.print('class Parser(LRParser):')
        self.print('    def __init__(self):')
        # Generate rules:
        self.print('        self.start_symbol = "{}"'.format(self.grammar.start_symbol))
        self.print('        self.grammar = Grammar({})'.format(self.grammar.terminals))
        for rule_number, rule in enumerate(self.grammar.productions):
            rule.f_name = 'action_{}_{}'.format(rule.name, rule_number)
            self.print('        self.grammar.add_production("{}", {}, self.{})'.format(rule.name, rule.symbols, rule.f_name))
        # Fill action table:
        self.print('        self.action_table = {}')
        for state in self.action_table:
            action = self.action_table[state]
            self.print('        self.action_table[{}] = {}'.format(state, action))
        self.print('')

        # Fill goto table:
        self.print('        self.goto_table = {}')
        for state_number in self.goto_table:
            to = self.goto_table[state_number]
            self.print('        self.goto_table[{}] = {}'.format(state_number, to))
        self.print('')

        # Generate a function for each action:
        for rule in self.grammar.productions:
            num_symbols = len(rule.symbols)
            args = ', '.join('arg{}'.format(n + 1) for n in range(num_symbols))
            self.print('    def {}(self, {}):'.format(rule.f_name, args))
            if rule.f == None:
                semantics = 'pass'
            else:
                semantics = str(rule.f)
                if semantics.strip() == '':
                    semantics = 'pass'
            for n in range(num_symbols):
                semantics = semantics.replace('${}'.format(n + 1), 'arg{}'.format(n + 1))
            self.print('        {}'.format(semantics))
            self.print('')


def make_argument_parser():
    # Parse arguments:
    parser = argparse.ArgumentParser(description='xacc compiler compiler')
    parser.add_argument('source', type=argparse.FileType('r'), \
      help='the parser specification')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), \
        default=sys.stdout)
    return parser


def load_as_module(filename):
    """ Load a parser spec file, generate LR tables and create module """
    ob = io.StringIO()
    args = argparse.Namespace(source=open(filename), output=ob)
    main(args)

    parser_mod = types.ModuleType('generated_parser')
    exec(ob.getvalue(), parser_mod.__dict__)
    return parser_mod


def main(args):
    src = args.source.read()
    args.source.close()

    # Construction of generator parts:
    lexer = XaccLexer()
    parser = XaccParser()
    generator = XaccGenerator()

    # Sequence source through the generator parts:
    lexer.feed(src)
    grammar = parser.parse_grammar(lexer)
    generator.generate(grammar, parser.headers, args.output)


if __name__ == '__main__':
    args = make_argument_parser().parse_args()
    main(args)
