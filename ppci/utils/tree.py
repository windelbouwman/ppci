"""

Implementation of tree structure. Including a parser that can
parse tree structures from text.

"""
from ppci.pcc.baselex import BaseLexer


class Tree:
    """ Tree node with a name and possibly some child nodes """

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

    def __getitem__(self, index):
        return self.children[index]

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
    """ Parser that can parse tree expressions. For example:

        A(B(1,2,3),2,1,C)
    """
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
