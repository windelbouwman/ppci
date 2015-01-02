
from ppci.baselex import BaseLexer


class Tree:
    """ Tree node with a name and possibly some child nodes """
    __slots__ = ['name', 'value', 'children', 'state']

    def __init__(self, name, *args, value=None):
        self.name = name
        self.value = value
        self.children = args

    def __repr__(self):
        if self.children:
            ch = ', '.join(str(c) for c in self.children)
            ch = '({})'.format(ch)
        else:
            ch = ''
        if self.value is not None:
            val = '[{}]'.format(self.value)
        else:
            val = ''
        return '{}{}{}'.format(self.name, val, ch)

    def structural_equal(self, other):
        return self.name == other.name and \
            len(self.children) == len(other.children) and \
            all(a.structural_equal(b) for a, b in
                zip(self.children, other.children))

    def get_defined_names(self):
        """ Returns a set of all names defined by this tree """
        names = set([self.name])
        for c in self.children:
            names = names | c.get_defined_names()
        return names


class TreeLexer(BaseLexer):
    def __init__(self):
        tok_spec = [
            ('ID', r'[A-Za-z][A-Za-z\d_]*', lambda typ, val: (typ, val)),
            ('SKIP', r'[ \t]', None),
            ('LEESTEKEN', r'[,\(\)]', lambda typ, val: (val, val))
            ]
        super().__init__(tok_spec)


class TreeParser:
    def __init__(self):
        self.lexer = TreeLexer()
        self.peak = None

    def pop(self):
        t = self.peak
        self.peak = self.lexer.next_token()
        return t

    def consume(self, typ):
        t = self.pop()
        assert t.typ == typ
        return t

    def has_consumed(self, typ):
        if self.peak.typ == typ:
            self.pop()
            return True
        return False

    def parse(self, s):
        self.lexer.feed(s)
        self.peak = self.lexer.next_token()
        return self.parse_tree()

    def parse_tree(self):
        name = self.consume('ID').val
        children = []
        if self.has_consumed('('):
            children.append(self.parse_tree())
            while self.has_consumed(','):
                children.append(self.parse_tree())
            self.consume(')')
        return Tree(name, *children)

tree_parser = TreeParser()


def from_string(s):
    """ Create tree from string definition """
    return tree_parser.parse(s)


class State:
    """ State used to label tree nodes """
    def __init__(self):
        self.labels = {}

    def has_goal(self, goal):
        return goal in self.labels

    def get_cost(self, goal):
        return self.labels[goal][0]

    def get_rule(self, goal):
        return self.labels[goal][1]

    def set_cost(self, goal, cost, rule):
        """
            Mark that this tree can be matched with a rule for a certain cost
        """
        if self.has_goal(goal):
            if self.get_cost(goal) > cost:
                self.labels[goal] = (cost, rule)
        else:
            self.labels[goal] = (cost, rule)


class BaseMatcher:
    """ Base class for matcher objects. """
    def kids(self, tree, rule):
        return self.kid_functions[rule](tree)

    def nts(self, rule):
        return self.nts_map[rule]

    def burm_label(self, tree):
        """ Label all nodes in the tree bottom up """
        for c in tree.children:
            self.burm_label(c)
        self.burm_state(tree)

    def apply_rules(self, tree, goal):
        rule = tree.state.get_rule(goal)
        results = [self.apply_rules(kid_tree, kid_goal)
                   for kid_tree, kid_goal in zip(self.kids(tree, rule), self.nts(rule))]
        return self.pat_f[rule](tree, *results)
