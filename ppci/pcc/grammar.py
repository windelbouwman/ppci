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

    def add_production(self, name, symbols, semantics=None):
        """ Add a production rule to the grammar """
        production = Production(name, symbols, semantics)
        self.productions.append(production)
        if name in self.terminals:
            raise ParserGenerationException(
                "Cannot redefine terminal {0}".format(name))
        self.nonterminals.add(name)

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
            eps = eps[0]
            print(eps)

            # Remove the rule
            self.productions.remove(eps)

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
    def __init__(self, name, symbols, semantics):
        self.name = name
        self.symbols = symbols
        self.f = semantics

    def __repr__(self):
        return '{0} -> {1}'.format(self.name, self.symbols)

    @property
    def is_epsilon(self):
        """ Checks if this rule is an epsilon rule """
        return len(self.symbols) == 0


def print_grammar(g):
    """ Pretty print a grammar """
    print(g)
    for production in g.productions:
        print(production)
