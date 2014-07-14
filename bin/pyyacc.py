"""
  Parser generator script
"""

from ppci import Token

EPS = 'EPS'
EOF = 'EOF'


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
    def __init__(self, terminals):
        self.terminals = set(terminals)
        self.nonterminals = set()
        self.productions = []
        self._first = None  # Cached first set
        self.start_symbol = None

    def __repr__(self):
        return 'Grammar with {} rules'.format(len(self.productions))

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

    def initialItemSet(self):
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

    def genCanonicalSet(self, iis):
        states = []
        worklist = []
        transitions = {}
        def addSt(s):
            if not (s in states):
                worklist.append(s)
                states.append(s)
        addSt(iis)
        while len(worklist) > 0:
            itemset = worklist.pop(0)
            for symbol in self.Symbols:
                nis = self.nextItemSet(itemset, symbol)
                if not nis:
                    continue
                addSt(nis)
                transitions[(states.index(itemset), symbol)] = states.index(nis)
        return states, transitions

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
        iis = self.initialItemSet()

        # First generate all item sets by using the nextItemset function:
        states, transitions = self.genCanonicalSet(iis)

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
                        raise ParserGenerationException('LR construction conflict {0} vs {1}'.format(a1, a2))
            else:
                action_table[key] = action

        # Fill action table:
        for state in states:
            # Detect conflicts:
            for item in state:
                if item.IsShift and item.Next in self.terminals:
                    # Rule 1, a shift item:
                    nextstate = transitions[(states.index(state), item.Next)]
                    setAction(states.index(state), item.Next, Shift(nextstate))
                if item.IsReduce:
                    if item.production.name == self.start_symbol and item.look_ahead == EOF:
                        # Rule 3: accept:
                        act = Accept(self.productions.index(item.production))
                    else:
                        # Rule 2, reduce item:
                        act = Reduce(self.productions.index(item.production))
                    setAction(states.index(state), item.look_ahead, act)
            for nt in self.nonterminals:
                key = (states.index(state), nt)
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
        action = ' ' + str(self.f) if self.f else ''
        return '{0} -> {1}'.format(self.name, self.symbols) + action


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
            if not key in self.action_table:
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

