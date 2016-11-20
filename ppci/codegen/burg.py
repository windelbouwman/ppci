#!/usr/bin/python

"""
Bottom up rewrite generator
---------------------------

This script takes as input a description of patterns and outputs a
matcher class that can match trees given the patterns.

Patterns are specified as follows::

     reg -> ADDI32(reg, reg) 2 (. add NT0 NT1 .)
     reg -> MULI32(reg, reg) 3 (. .)

or a multiply add::

    reg -> ADDI32(MULI32(reg, reg), reg) 4 (. muladd $1, $2, $3 .)

The general specification pattern is::

    [result] -> [tree] [cost] [template code]

Trees
-----

A tree is described using parenthesis notation. For example a node X with
three child nodes is described as:

     X(a, b, b)

Trees can be nested:

     X(Y(a, a), a)

The 'a' in the example above indicates an open connection to a next tree
pattern.


In the example above 'reg' is a non-terminal. ADDI32 is a terminal.
non-terminals
cannot have child nodes. A special case occurs in this case:

    reg -> rc

where 'rc' is a non-terminal. This is an example of a chain rule. Chain rules
can be used to allow several variants of non-terminals.

The generated matcher uses dynamic programming to find the best match of the
tree. This strategy consists of two steps:

  - label: During this phase the given tree is traversed in a bottom up way.
    each node is labelled with a possible matching rule and the corresponding
    cost.
  - select: In this step, the tree is traversed again, selecting at each point
    the cheapest way to get to the goal.

"""

import sys
from os import path
import argparse
from ppci.common import Token, SourceLocation
from ppci.pcc import baselex, yacc
from ppci.utils.tree import Tree

# Generate parser on the fly:
spec_file = path.join(path.dirname(path.abspath(__file__)), 'burg.grammar')
burg_parser = yacc.load_as_module(spec_file)


class BurgLexer(baselex.BaseLexer):
    """ Overridden base lexer to keep track of sections """
    def __init__(self):
        tok_spec = [
           ('id', r'[A-Za-z][A-Za-z\d_]*', lambda typ, val: (typ, val)),
           ('kw', r'%[A-Za-z][A-Za-z\d_]*', lambda typ, val: (val, val)),
           ('number', r'\d+', lambda typ, val: (typ, int(val))),
           ('STRING', r"'[^']*'", lambda typ, val: ('string', val[1:-1])),
           ('OTHER', r'[:;\|\(\),]', lambda typ, val: (val, val)),
           ('SKIP', r'[ ]', None)
            ]
        super().__init__(tok_spec)

    def tokenize(self, txt):
        lines = txt.split('\n')
        header_lines = []
        section = 0
        for line in lines:
            loc = SourceLocation(self.filename, 0, 0, 0)
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            elif line == '%%':
                section += 1
                if section == 1:
                    yield Token('header', header_lines, loc)
                yield Token('%%', '%%', loc)
            else:
                if section == 0:
                    header_lines.append(line)
                else:
                    # we could use yield from below, but python 3.2 does not
                    # work then:
                    for tk in super().tokenize(line):
                        yield tk


class Rule:
    """ A rewrite rule. Specifies a tree that can be rewritten into a result
    at a specific cost """
    def __init__(self, non_term, tree, cost, acceptance, template):
        self.non_term = non_term
        self.tree = tree
        self.cost = cost
        self.acceptance = acceptance
        self.template = template
        self.nr = 0

    def __repr__(self):
        return '{} -> {} ${}'.format(self.non_term, self.tree, self.cost)


class Symbol:
    def __init__(self, name):
        self.name = name


class Term(Symbol):
    pass


class Nonterm(Symbol):
    def __init__(self, name):
        super().__init__(name)
        self.chain_rules = []


class BurgSystem:
    def __init__(self):
        self.rules = []
        self.symbols = {}
        self.rule_map = {}
        self.goal = None

    def sym_of_type(self, t):
        return (s.name for s in self.symbols.values() if type(s) is t)

    terminals = property(lambda s: s.sym_of_type(Term))
    non_terminals = property(lambda s: s.sym_of_type(Nonterm))

    def add_rule(self, non_term, tree, cost, acceptance, template):
        if type(template) is str:
            template = template.strip()
        if not template:
            template = 'pass'
        rule = Rule(non_term, tree, cost, acceptance, template)
        if len(tree.children) == 0 and tree.name not in self.terminals:
            self.non_term(tree.name).chain_rules.append(rule)
        self.non_term(rule.non_term)
        self.rules.append(rule)
        rule.nr = len(self.rules)

        # Register the rule in the rule map:
        self.rule_map[tree.name].append(rule)
        return rule

    def get_rule(self, nr):
        """ Get a rule by rule number """
        rule = self.rules[nr - 1]
        assert rule.nr == nr
        return rule

    def get_rules_for_root(self, name):
        """ Get only the rules for a given root name """
        return self.rule_map[name]

    def non_term(self, name):
        if name in self.terminals:
            raise BurgError('Cannot redefine terminal')
        if not self.goal:
            self.goal = name
        return self.install(name, Nonterm)

    def tree(self, name, *args):
        return Tree(name, *args)

    def chain_rules_for_nt(self, nt):
        return self.symbols[nt].chain_rules

    def install(self, name, t):
        assert type(name) is str
        if name in self.symbols:
            assert type(self.symbols[name]) is t
        else:
            self.symbols[name] = t(name)
            self.rule_map[name] = list()
        return self.symbols[name]

    def add_terminal(self, terminal):
        self.install(terminal, Term)

    def tree_terminal_equal(self, t1, t2):
        """ Check if the terminals of a tree match """
        if t1.name in self.terminals and t2.name in self.terminals:
            if t1.name == t2.name:
                # match children:
                return all(self.tree_terminal_equal(a, b) for a, b in
                           zip(t1.children, t2.children))
            else:
                return False
        else:
            # We hit an open end
            assert t1.name in self.non_terminals or \
                t2.name in self.non_terminals
            return True

    def get_kids(self, tree, template_tree):
        """ Get the kids of a tree given a template that matched """
        kids = []
        if template_tree.name in self.non_terminals:
            assert len(template_tree.children) == 0
            kids.append(tree)
        else:
            for t, tt in zip(tree.children, template_tree.children):
                kids.extend(self.get_kids(t, tt))
        return kids

    def get_nts(self, template_tree):
        """ Get the names of the non terminals of a template """
        nts = []
        if template_tree.name in self.non_terminals:
            assert len(template_tree.children) == 0
            nts.append(template_tree.name)
        else:
            for tt in template_tree.children:
                nts.extend(self.get_nts(tt))
        return nts

    def check_tree_defined(self, tree):
        """ Check if all names in a tree are defined """
        for name in tree.get_defined_names():
            if name not in self.symbols.keys():
                raise BurgError("{} not defined".format(name))

    def check(self):
        """ Run sanity checks on this burg system """
        for rule in self.rules:
            self.check_tree_defined(rule.tree)
        # Check burg system for completeness:
        # print(self.sys.non_terminals)

        # TODO: check if all possible code can be covered.


class BurgError(Exception):
    pass


class BurgParser(burg_parser.Parser):
    """ Derived from automatically generated parser """
    def parse(self, l):
        self.system = BurgSystem()
        super().parse(l)
        return self.system


class BurgGenerator:
    def print(self, level, text=''):
        """ Print helper function that prints to output file """
        print('    ' * level + text, file=self.output_file)

    def generate(self, system, output_file):
        """ Generate script that implements the burg spec """
        self.output_file = output_file
        self.system = system

        self.print(0, '#!/usr/bin/python')
        self.print(
            0, 'from ppci.codegen.treematcher import BaseMatcher, State')
        self.print(0, 'from ppci.utils.tree import Tree')
        for header in self.system.header_lines:
            self.print(0, header)
        self.print(0)
        self.print(0, 'class Matcher(BaseMatcher):')
        self.print(1, 'def __init__(self):')
        self.print(2, 'self.kid_functions = {}')
        self.print(2, 'self.nts_map = {}')
        self.print(2, 'self.pat_f = {}')
        for rule in self.system.rules:
            kids, dummy = self.compute_kids(rule.tree, 't')
            rule.num_nts = len(dummy)
            lf = 'lambda t: [{}]'.format(', '.join(kids), rule)
            pf = 'self.P{}'.format(rule.nr)
            self.print(0)
            self.print(2, '# {}: {}'.format(rule.nr, rule))
            self.print(2, 'self.kid_functions[{}] = {}'.format(rule.nr, lf))
            self.print(2, 'self.nts_map[{}] = {}'.format(rule.nr, dummy))
            self.print(2, 'self.pat_f[{}] = {}'.format(rule.nr, pf))
        self.print(0)
        for rule in self.system.rules:
            if rule.num_nts > 0:
                args = ', '.join('c{}'.format(x) for x in range(rule.num_nts))
                args = ', ' + args
            else:
                args = ''
            # Create template function:
            self.print(0)
            self.print(1, 'def P{}(self, tree{}):'.format(rule.nr, args))
            template = rule.template
            for t in template.split(';'):
                self.print(2, '{}'.format(t.strip()))
            # Create acceptance function:
            if rule.acceptance:
                self.print(0)
                self.print(1, 'def A{}(self, tree):'.format(rule.nr))
                for t in rule.acceptance.split(';'):
                    self.print(2, '{}'.format(t.strip()))
        self.emit_state()
        self.print(1, 'def gen(self, tree):')
        self.print(2, 'self.burm_label(tree)')
        self.print(
            2, 'if not tree.state.has_goal("{}"):'.format(self.system.goal))
        self.print(3, 'raise Exception("Tree {} not covered".format(tree))')
        self.print(
            2, 'return self.apply_rules(tree, "{}")'.format(self.system.goal))

    def emit_record(self, rule, state_var):
        # TODO: check for rules fullfilled (by not using 999999)
        acc = ''
        if rule.acceptance:
            acc = ' and self.A{}(tree)'.format(rule.nr)
        self.print(3, 'nts = self.nts({})'.format(rule.nr))
        self.print(3, 'kids = self.kids(tree, {})'.format(rule.nr))
        self.print(
            3,
            'if all(x.state.has_goal(y) for x, y in zip(kids, nts)){}:'.format(
                acc))
        self.print(
            4,
            ('c = sum(x.state.get_cost(y) for x, y in zip(kids, nts)) + {}')
            .format(rule.cost))
        self.print(
            4, 'tree.state.set_cost("{}", c, {})'.format(
                rule.non_term, rule.nr))
        for cr in self.system.symbols[rule.non_term].chain_rules:
            self.print(4, '# Chain rule: {}'.format(cr))
            self.print(
                4, 'tree.state.set_cost("{}", c + {}, {})'.format(
                    cr.non_term, cr.cost, cr.nr))

    def emit_state(self):
        """ Emit a function that assigns a new state to a node """
        self.print(1, 'def burm_state(self, tree):')
        self.print(2, 'tree.state = State()')
        for term in self.system.terminals:
            self.emitcase(term)
        self.print(0)

    def emitcase(self, term):
        rules = [rule for rule in self.system.rules if rule.tree.name == term]
        for rule in rules:
            condition = self.emittest(rule.tree, 'tree')
            self.print(2, 'if {}:'.format(condition))
            self.emit_record(rule, 'state')

    def compute_kids(self, t, root_name):
        """ Compute of a pattern the blanks that must be provided
        from below in the tree """
        if t.name in self.system.non_terminals:
            return [root_name], [t.name]
        else:
            k = []
            nts = []
            for i, c in enumerate(t.children):
                pfx = root_name + '.children[{}]'.format(i)
                kf, dummy = self.compute_kids(c, pfx)
                nts.extend(dummy)
                k.extend(kf)
            return k, nts

    def emittest(self, tree, prefix):
        """ Generate condition for a tree pattern """
        ct = (
            c for c in tree.children
            if c.name not in self.system.non_terminals)
        child_tests = (
            self.emittest(c, prefix + '.children[{}]'.format(i))
            for i, c in enumerate(ct))
        child_tests = ('({})'.format(ct) for ct in child_tests)
        child_tests = ' and '.join(child_tests)
        child_tests = ' and ' + child_tests if child_tests else ''
        tst = '{}.name == "{}"'.format(prefix, tree.name)
        return tst + child_tests


def make_argument_parser():
    """ Constructs an argument parser """
    parser = argparse.ArgumentParser(
        description='pyburg bottom up rewrite system generator')
    parser.add_argument(
        'source', type=argparse.FileType('r'), help='the parser specification')
    parser.add_argument(
        '-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    return parser


def main(args):
    src = args.source.read()
    args.source.close()

    # Parse specification into burgsystem:
    l = BurgLexer()
    p = BurgParser()
    l.feed(src)
    burg_system = p.parse(l)

    # Generate matcher:
    generator = BurgGenerator()
    generator.generate(burg_system, args.output)


if __name__ == '__main__':
    # Parse arguments:
    args = make_argument_parser().parse_args()
    main(args)
