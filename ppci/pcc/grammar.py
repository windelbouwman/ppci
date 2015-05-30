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

    def add_terminals(self, names):
        for name in names:
            self.add_terminal(name)

    def add_terminal(self, name):
        """ Add a terminal name """
        if name in self.nonterminals:
            raise ParserGenerationException(
                "Cannot redefine non-terminal {0} as terminal".format(name))
        self.terminals.add(name)

    def add_production(self, name, symbols, f=None):
        """ Add a production rule to the grammar """
        production = Production(name, symbols, f)
        self.productions.append(production)
        if name in self.terminals:
            raise ParserGenerationException(
                "Cannot redefine terminal {0}".format(name))
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

    def productions_for_name(self, name):
        """ Retrieve all productions for a non terminal """
        return [p for p in self.productions if p.name == name]

    @property
    def Symbols(self):
        """ Get all the symbols defined by this grammar """
        return self.nonterminals | self.terminals

    def add_state(self, s):
        pass

    def check_symbols(self):
        """ Checks no symbols are undefined """
        for production in self.productions:
            for symbol in production.symbols:
                if symbol not in self.Symbols:
                    raise ParserGenerationException(
                        'Symbol {0} undefined'.format(symbol))


class Production:
    """ Production rule for a grammar. It consists of a left hand side
        non-terminal and a list of symbols as right hand side. Also it
        contains a function that must be called when this rule is applied.
        The right hand side may contain terminals and non-terminals.
    """
    def __init__(self, name, symbols, f):
        self.name = name
        self.symbols = symbols
        self.f = f

    def __repr__(self):
        return '{0} -> {1}'.format(self.name, self.symbols)


def print_grammar(g):
    """ Pretty print a grammar """
    print(g)
    for production in g.productions:
        print(production)


