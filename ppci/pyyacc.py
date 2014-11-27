"""
  Parser generator script
"""

import types
import io
import datetime
import logging
from collections import namedtuple

from ppci.baselex import BaseLexer, EPS, EOF
from ppci import Token, SourceLocation


class ParserGenerationException(Exception):
    """ Raised when something goes wrong during parser generation """
    pass


class ParserException(Exception):
    """ Raised during a failure in the parsing process """
    pass


class Action:
    def __repr__(self):
        return 'Action'

    def __eq__(self, other):
        return str(self) == str(other)


class Shift(Action):
    def __init__(self, to_state):
        self.to_state = to_state

    def __repr__(self):
        return 'Shift({})'.format(self.to_state)


class Reduce(Action):
    def __init__(self, rule):
        self.rule = rule

    def __repr__(self):
        return 'Reduce({})'.format(self.rule)


class Accept(Reduce):
    def __repr__(self):
        return 'Accept({})'.format(self.rule)


def print_grammar(g):
    """ Pretty print a grammar """
    print(g)
    for production in g.productions:
        print(production)


def calculate_first_sets(grammar):
    """
        Calculate first sets for each grammar symbol
        This is a dictionary which maps each grammar symbol
        to a set of terminals that can be encountered first
        when looking for the symbol.
    """
    first = {}
    nullable = {}
    for terminal in grammar.terminals | {EOF, EPS}:
        first[terminal] = set([terminal])
        nullable[terminal] = False
    for nt in grammar.nonterminals:
        first[nt] = set()
        nullable[nt] = False
    while True:
        some_change = False
        for rule in grammar.productions:
            # Check for null-ability:
            if all(nullable[beta] for beta in rule.symbols):
                if not nullable[rule.name]:
                    nullable[rule.name] = True
                    some_change = True
            # Update first sets:
            for beta in rule.symbols:
                if not nullable[beta]:
                    if first[beta] - first[rule.name]:
                        first[rule.name] |= first[beta]
                        some_change = True
                    break
        if not some_change:
            break
    return first


class Grammar:
    """ Defines a grammar of a language """
    def __init__(self, terminals=set()):
        self.terminals = set(terminals)
        self.nonterminals = set()
        self.productions = []
        self._first = None  # Cached first set
        self.start_symbol = None

    def __repr__(self):
        return 'Grammar with {} rules'.format(len(self.productions))

    def add_terminals(self, names):
        for name in names:
            self.add_terminal(name)

    def add_terminal(self, name):
        """ Add a terminal name """
        if name in self.nonterminals:
            raise ParserGenerationException("Cannot redefine non-terminal {0} as terminal".format(name))
        self.terminals.add(name)

    def add_production(self, name, symbols, f=None):
        """ Add a production rule to the grammar """
        production = Production(name, symbols, f)
        self.productions.append(production)
        if name in self.terminals:
            raise ParserGenerationException("Cannot redefine terminal {0}".format(name))
        self.nonterminals.add(name)
        self._first = None  # Invalidate cached version

    def add_one_or_more(self, element_nonterm, list_nonterm):
        """ Helper to add the rule
           lst: elem
           lst: lst elem
        """
        def a(el):
            return [el]

        def b(ls, el):
            ls.append(el)
            return ls
        self.add_production(list_nonterm, [element_nonterm], a)
        self.add_production(list_nonterm, [list_nonterm, element_nonterm], b)

    def productionsForName(self, name):
        """ Retrieve all productions for a non terminal """
        return [p for p in self.productions if p.name == name]

    @property
    def Symbols(self):
        """ Get all the symbols defined by this grammar """
        return self.nonterminals | self.terminals

    @property
    def first(self):
        """
          The first set is a mapping from a grammar symbol to a set of
          set of all terminal symbols that can be the first terminal when
          looking for the grammar symbol
        """
        if not self._first:
            self._first = calculate_first_sets(self)
        return self._first

    def closure(self, itemset):
        """ Expand itemset by using epsilon moves """
        worklist = list(itemset)
        def addIt(itm):
            if not itm in itemset:
                itemset.add(itm)
                worklist.append(itm)
        def first2(itm):
            # When using the first sets, create a copy:
            f = set(self.first[itm.NextNext])
            if EPS in f:
                f.discard(EPS)
                f.add(itm.look_ahead)
            return f
        # Start of algorithm:
        while worklist:
            item = worklist.pop(0)
            if not item.IsShift:
                continue
            if not (item.Next in self.nonterminals):
                continue
            C = item.Next
            for add_p in self.productionsForName(C):
                for b in first2(item):
                    addIt(Item(add_p, 0, b))
        return frozenset(itemset)

    def initial_item_set(self):
        """ Calculates the initial item set """
        iis = set()
        for p in self.productionsForName(self.start_symbol):
            iis.add(Item(p, 0, EOF))
        return self.closure(iis)

    def nextItemSet(self, itemset, symbol):
        """
            Determines the next itemset for the current set and a symbol
            This is the goto procedure
        """
        next_set = set()
        for item in itemset:
            if item.can_shift_over(symbol):
                next_set.add(item.shifted())
        return self.closure(next_set)

    def add_state(self, s):
        pass

    def gen_canonical_set(self, iis):
        states = set()
        worklist = []
        transitions = {}
        indici = {}
        def addSt(s):
            if s not in states:
                worklist.append(s)
                indici[s] = len(indici)
                states.add(s)
        addSt(iis)
        while len(worklist) > 0:
            itemset = worklist.pop(0)
            for symbol in self.Symbols:
                nis = self.nextItemSet(itemset, symbol)
                if not nis:
                    continue
                addSt(nis)
                transitions[(indici[itemset], symbol)] = indici[nis]
        return states, transitions, indici

    def checkSymbols(self):
        """ Checks no symbols are undefined """
        for production in self.productions:
            for symbol in production.symbols:
                if symbol not in self.Symbols:
                    raise ParserGenerationException('Symbol {0} undefined'.format(symbol))

    def generate_parser(self):
        """ Generates a parser from the grammar """
        action_table, goto_table = self.generate_tables()
        p = LRParser(action_table, goto_table, self.start_symbol)
        p.grammar = self
        return p

    def generate_tables(self):
        """ Generate parsing tables """
        if not self.start_symbol:
            self.start_symbol = self.productions[0].name
        self.checkSymbols()
        action_table = {}
        goto_table = {}
        iis = self.initial_item_set()

        # First generate all item sets by using the nextItemset function:
        states, transitions, indici = self.gen_canonical_set(iis)

        def setAction(state, t, action):
            assert isinstance(action, Action)
            key = (state, t)
            assert type(state) is int
            assert type(t) is str
            if key in action_table:
                action2 = action_table[key]
                if action != action2:
                    if (type(action2) is Reduce) and (type(action) is Shift):
                        # Automatically resolve and do the shift action!
                        # Simple, but almost always what you want!!
                        action_table[key] = action
                    elif isinstance(action2, Shift) and isinstance(action, Reduce):
                        pass
                    else:
                        a1 = str(action)
                        a2 = str(action2)
                        prod = self.productions[action.rule]
                        prod2 = self.productions[action2.rule]
                        raise ParserGenerationException('LR construction conflict {} vs {} ({} vs {})'.format(a1, a2, prod, prod2))
            else:
                action_table[key] = action

        # Fill action table:
        for state in states:
            state_nr = indici[state]
            # Detect conflicts:
            for item in state:
                if item.IsShift and item.Next in self.terminals:
                    # Rule 1, a shift item:
                    nextstate = transitions[(state_nr, item.Next)]
                    setAction(state_nr, item.Next, Shift(nextstate))
                if item.IsReduce:
                    if item.production.name == self.start_symbol and item.look_ahead == EOF:
                        # Rule 3: accept:
                        act = Accept(self.productions.index(item.production))
                    else:
                        # Rule 2, reduce item:
                        act = Reduce(self.productions.index(item.production))
                    setAction(state_nr, item.look_ahead, act)
            for nt in self.nonterminals:
                key = (state_nr, nt)
                if key in transitions:
                    goto_table[key] = transitions[key]
        return action_table, goto_table


class Production:
    """ Production rule for a grammar """
    def __init__(self, name, symbols, f):
        self.name = name
        self.symbols = symbols
        self.f = f

    def __repr__(self):
        return '{0} -> {1}'.format(self.name, self.symbols)


class Item:
    """
        Represents a partially parsed item
        It has a production it is looking for, a position
        in this production called the 'dot' and a look ahead
        symbol that must follow this item.
    """
    def __init__(self, production, dotpos, look_ahead):
        self.production = production
        self.dotpos = dotpos
        assert self.dotpos <= len(self.production.symbols)
        self.look_ahead = look_ahead
        self._is_shift = self.dotpos < len(self.production.symbols)
        self.IsShift = self._is_shift
        if self.IsShift:
            self.Next = self.production.symbols[self.dotpos]
        self._data = (self.production, self.dotpos, self.look_ahead)
        self._hash = self._data.__hash__()

    def __eq__(self, other):
        if type(other) is type(self):
            return self._data == other._data
        return False

    def __hash__(self):
        return self._hash

    @property
    def IsReduce(self):
        """ Check if this item has the dot at the end """
        return not self._is_shift

    def can_shift_over(self, symbol):
        """ Determines if this item can shift over the given symbol """
        return self._is_shift and self.Next == symbol

    def shifted(self):
        """ Creates a new item that is shifted one position """
        return Item(self.production, self.dotpos + 1, self.look_ahead)

    @property
    def NextNext(self):
        """ Gets the symbol after the next symbol, or EPS if at the end """
        if self.dotpos + 1 >= len(self.production.symbols):
            return EPS
        else:
            return self.production.symbols[self.dotpos + 1]

    def __repr__(self):
        prod = self.production
        predot = ' '.join(prod.symbols[0:self.dotpos])
        postdot = ' '.join(prod.symbols[self.dotpos:])
        name = prod.name
        args = (name, predot, postdot, self.look_ahead)
        return '[{0} -> {1} . {2} -> {3}]'.format(*args)


class LRParser:
    """ LR parser automata. This class takes goto and action table
        and can then process a sequence of tokens.
    """
    def __init__(self, action_table, goto_table, start_symbol):
        self.action_table = action_table
        self.goto_table = goto_table
        self.start_symbol = start_symbol

    def parse(self, lexer):
        """ Parse an iterable with tokens """
        assert hasattr(lexer, 'next_token'), '{0} is no lexer'.format(type(lexer))
        stack = [0]
        r_data_stack = []
        look_ahead = lexer.next_token()
        assert type(look_ahead) is Token
        # TODO: exit on this condition:
        while stack != [0, self.start_symbol, 0]:
            state = stack[-1]   # top of stack
            key = (state, look_ahead.typ)
            if key not in self.action_table:
                raise ParserException('Error parsing at character {0}'.format(look_ahead))
            action = self.action_table[key]
            if type(action) is Reduce:
                f_args = []
                prod = self.grammar.productions[action.rule]
                for s in prod.symbols:
                    stack.pop()
                    stack.pop()
                    f_args.append(r_data_stack.pop())
                f_args.reverse()
                r_data = None
                if prod.f:
                    r_data = prod.f(*f_args)
                state = stack[-1]
                stack.append(prod.name)
                stack.append(self.goto_table[(state, prod.name)])
                r_data_stack.append(r_data)
            elif type(action) is Shift:
                stack.append(look_ahead.typ)
                stack.append(action.to_state)
                r_data_stack.append(look_ahead)
                look_ahead = lexer.next_token()
                assert type(look_ahead) is Token
            elif type(action) is Accept:
                # Pop last rule data off the stack:
                f_args = []
                param = self.grammar.productions[action.rule]
                for s in param.symbols:
                    stack.pop()
                    stack.pop()
                    f_args.append(r_data_stack.pop())
                f_args.reverse()
                if param.f:
                    ret_val = param.f(*f_args)
                else:
                    ret_val = None
                # Break out!
                stack.append(param.name)
                stack.append(0)
                break
        # At exit, the stack must be 1 long
        # TODO: fix that this holds:
        #assert stack == [0, self.start_symbol, 0]
        return ret_val


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
        self.print('from ppci.pyyacc import LRParser, Reduce, Shift, Accept, Production, Grammar')
        self.print('from ppci import Token')
        self.print('')
        for h in self.headers:
            self.print(h)
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
            if num_symbols > 0:
                args = ', '.join('arg{}'.format(n + 1) for n in range(num_symbols))
                self.print('    def {}(self, {}):'.format(rule.f_name, args))
            else:
                self.print('    def {}(self):'.format(rule.f_name))

            if rule.f is None:
                semantics = 'pass'
            else:
                semantics = str(rule.f)
                if semantics.strip() == '':
                    semantics = 'pass'
            for n in range(num_symbols):
                semantics = semantics.replace('${}'.format(n + 1), 'arg{}'.format(n + 1))
            self.print('        {}'.format(semantics))
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


def main(args):
    transform(args.source, args.output)


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
