from .common import ParserGenerationException


class Grammar:
    """ Defines a grammar of a language """
    def __init__(self):
        self.terminals = set()
        self.nonterminals = set()
        self.productions = []
        self.start_symbol = None

    def __repr__(self):
        return 'Grammar with {} rules and {} terminals'.format(
            len(self.productions), len(self.terminals))

    def add_terminals(self, terminals):
        """ Add all terminals to terminals for this grammar """
        for terminal in terminals:
            self.add_terminal(terminal)

    def add_terminal(self, name):
        """ Add a terminal name """
        if name in self.nonterminals:
            raise ParserGenerationException(
                "Cannot redefine non-terminal {0} as terminal".format(name))
        self.terminals.add(name)

    def add_production(self, name, symbols, semantics=None, priority=0):
        """ Add a production rule to the grammar """
        production = Production(name, symbols, semantics, priority=priority)
        self.productions.append(production)
        if name in self.terminals:
            raise ParserGenerationException(
                "Cannot redefine terminal {0}".format(name))
        self.nonterminals.add(name)

    def dump(self):
        """ Print this grammar """
        print_grammar(self)

    def add_one_or_more(self, element_nonterm, list_nonterm):
        """ Helper to add the rule
           lst: elem
           lst: lst elem
        """
        def a(el):
            return [el]

        self.add_production(list_nonterm, [element_nonterm], a)

        def b(ls, el):
            ls.append(el)
            return ls
        self.add_production(list_nonterm, [list_nonterm, element_nonterm], b)

    def productions_for_name(self, name):
        """ Retrieve all productions for a non terminal """
        return [p for p in self.productions if p.name == name]

    @property
    def symbols(self):
        """ Get all the symbols defined by this grammar """
        return self.nonterminals | self.terminals

    def is_terminal(self, name):
        """ Check if a name is a terminal """
        return name in self.terminals

    def is_nonterminal(self, name):
        """ Check if a name is a non-terminal """
        return name in self.nonterminals

    def rewrite_eps_productions(self):
        """ Make the grammar free of empty productions.
            Do this by permutating all combinations of rules that would
            otherwise contain an empty place.
        """
        while True:
            eps = [rule for rule in self.productions if rule.is_epsilon]
            if not eps:
                # We are done!
                break

            # Process the first occasion:
            eps_rule = eps[0]

            # Remove the epsilon-rule
            self.productions.remove(eps_rule)

            # For each rule containing the empty production, create new rules:
            for rule in self.productions:
                if eps_rule.name in rule.symbols:
                    self.create_combinations(rule, eps_rule.name)

    def create_combinations(self, rule, non_terminal):
        """ Create n copies of rule where nt is removed.
            For example replace:
            A -> B C B
            by:
            A -> B C B
            A -> B C
            A -> C B
            A -> C
            if:
            B -> epsilon
        """
        count = rule.symbols.count(non_terminal)
        # TODO: refactor this restriction:
        assert count == 1

        rhs = []
        for x in rule.symbols:
            if x == non_terminal:
                pass
            else:
                rhs.append(x)
        self.add_production(rule.name, rhs)
        # self.productions.remove(rule)

    @property
    def is_normal(self):
        """ Check if this grammar is normal.
            Which means:
            - No empty productions (epsilon productions)
        """
        # If the grammar contains an epsilon production, it is not normal:
        if any(rule.is_epsilon for rule in self.productions):
            return False

        return True

    def check_symbols(self):
        """ Checks no symbols are undefined """
        for production in self.productions:
            if production.is_epsilon:
                # raise ParserGenerationException("Epsilon!")
                pass
            for symbol in production.symbols:
                if symbol not in self.symbols:
                    raise ParserGenerationException(
                        'Symbol {0} undefined'.format(symbol))


class Production:
    """ Production rule for a grammar. It consists of a left hand side
        non-terminal and a list of symbols as right hand side. Also it
        contains a function that must be called when this rule is applied.
        The right hand side may contain terminals and non-terminals.
    """
    def __init__(self, name, symbols, semantics, priority=0):
        self.name = name
        self.symbols = tuple(symbols)
        self.f = semantics
        self.priority = priority

    def __repr__(self):
        return '{} -> {} P_{}'.format(self.name, self.symbols, self.priority)

    @property
    def is_epsilon(self):
        """ Checks if this rule is an epsilon rule """
        return len(self.symbols) == 0


def print_grammar(g):
    """ Pretty print a grammar """
    print(g)
    for production in g.productions:
        print(production)
