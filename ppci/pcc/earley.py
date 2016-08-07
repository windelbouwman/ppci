"""
Implementation of the earley parser strategy.

See also:
- https://en.wikipedia.org/wiki/Earley_parser

And the book:
Parsing Techniques: A Practical Guide (2nd edition)
"""

from ..common import ParseError


class Item:
    """ Partially parsed grammar rule """
    def __init__(self, rule, dot, origin):
        self.rule = rule
        self.dot = dot
        self.origin = origin

    @property
    def is_reduce(self):
        return not self.is_shift

    @property
    def is_shift(self):
        return self.dot < len(self.rule.symbols)

    def shifted(self):
        assert self.is_shift
        return Item(self.rule, self.dot + 1, self.origin)

    @property
    def nxt(self):
        return self.rule.symbols[self.dot]

    def __repr__(self):
        symbols = ["'{}'".format(symbol) for symbol in self.rule.symbols]
        if self.is_shift:
            dot_part1 = ' '.join(symbols[:self.dot])
            dot_part2 = ' '.join(symbols[self.dot:])
            dot_part = dot_part1 + ' . ' + dot_part2
        else:
            dot_part = ' '.join(symbols) + ' .'
        return '{} -> {}, {}'.format(self.rule.name, dot_part, self.origin)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return (
            self.rule.name,
            self.rule.symbols,
            self.rule.priority,
            self.dot,
            self.origin).__hash__()


class Column:
    """ A set of partially parsed items for a given token position """
    def __init__(self, i, token):
        self.i = i
        self.token = token
        self.items = set()
        self.item_list = list()

    def __iter__(self):
        return iter(self.item_list)

    def __repr__(self):
        return 'Column at {}'.format(self.token)

    def add(self, item):
        if item not in self.items:
            self.items.add(item)
            self.item_list.append(item)


def make_tokens(tokens):
    # Start with an non-token column!
    yield None
    token = tokens.next_token()
    while token.typ != 'EOF':
        yield token
        token = tokens.next_token()


class EarleyParser:
    """
        As opposed to an LR parser, the Earley parser does not construct
        tables from a grammar. It uses the grammar when parsing.

        THe Earley parser has 3 key functions:
        - predict: what have we parsed so far, and what productions can be
          made with this.
        - scan: parse the next input symbol, en create a new set of possible
          parsings
        - complete: when we have scanned something according to a rule, this
          rule can be applied.

        When an earley parse is complete, the parse can be back-tracked to
        yield the resulting parse tree or the syntax tree.
    """
    def __init__(self, grammar):
        self.grammar = grammar
        self.states = []

    def predict(self, item, col):
        """ Add all rules for a certain non-terminal """
        nx = item.nxt
        assert self.grammar.is_nonterminal(nx)
        for rule in self.grammar.productions_for_name(nx):
            new_item = Item(rule, 0, col.i)
            col.add(new_item)

    def scan(self, item, col):
        """ Check if the item can be shifted into the next column """
        if item.nxt == col.token.typ:
            col.add(item.shifted())

    def complete(self, completed_item, start_col, current_column):
        """ Complete a rule, check if any other rules can be shifted! """
        assert completed_item.is_reduce
        worklist = list(start_col)
        while worklist:
            item = worklist.pop(0)
            if item.is_shift and item.nxt == completed_item.rule.name:
                new_item = item.shifted()
                current_column.add(new_item)
                if current_column is start_col:
                    worklist.append(new_item)

    def parse(self, tokens, debug_dump=False):
        """ Parse the given token string """

        # Create the state stack:
        columns = [Column(i, tok) for i, tok in enumerate(make_tokens(tokens))]
        for rule in self.grammar.productions_for_name(
                self.grammar.start_symbol):
            columns[0].add(Item(rule, 0, 0))

        # Loop through all input.
        for col in columns:
            # print(col)
            processed_items = set()
            while processed_items != col.items:
                item = iter(col.items - processed_items).__next__()
                if item.is_shift:
                    if self.grammar.is_nonterminal(item.nxt):
                        self.predict(item, col)
                    elif col.i + 1 < len(columns):
                        self.scan(item, columns[col.i + 1])
                else:
                    self.complete(item, columns[item.origin], col)
                processed_items.add(item)

        # Check if the parse was a success:
        last_column = columns[-1]
        for item in last_column:
            if item.is_reduce and \
                    item.rule.name == self.grammar.start_symbol and \
                    item.origin == 0:
                break
        else:
            # self.dump_parse(columns)
            raise ParseError('Parsing failed')

        if debug_dump:
            self.dump_parse(columns)

        # Reconstruct the parse tree:
        return self.make_tree(columns, self.grammar.start_symbol)

    def make_tree(self, columns, nt):
        """ Make a parse tree """
        # print('Top tree item:', nt)
        tree, end = self.walk(columns, len(columns) - 1, nt)
        assert end == 0
        return tree

    def walk(self, columns, end, nt):
        """ Process the parsed columns back to a parse tree """
        items = columns[end]
        items = filter(lambda i: i.rule.name == nt and i.is_reduce, items)
        items = sorted(items, key=lambda i: i.rule.priority)
        if not items:
            raise RuntimeError("Unable build tree")  # pragma: no cover

        # We found an item
        item = items[0]
        r = []
        # assert len(item.rule.symbols) > 0
        for x in reversed(item.rule.symbols):
            if self.grammar.is_nonterminal(x):
                x, end = self.walk(columns, end, x)
                r.insert(0, x)
            else:
                r.insert(0, columns[end].token)
                end -= 1

        # Apply semantics, if any!
        if item.rule.f:
            res = item.rule.f(*r)
        else:
            res = None
        return res, end

    def dump_parse(self, columns):
        print("Parse result:")
        for col in columns:
            print("  {}".format(col))
            for item in col:
                print("    {}".format(item))
