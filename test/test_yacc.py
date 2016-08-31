import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import io
from ppci.pcc.grammar import Grammar, print_grammar
from ppci.pcc.common import ParserGenerationException
from ppci.pcc.lr import Item
from ppci.pcc.common import ParserException
from ppci.pcc.yacc import load_as_module, transform
from ppci.pcc.lr import calculate_first_sets
from ppci.common import Token, SourceLocation, CompilerError
from ppci.pcc.lr import LrParserBuilder
from ppci.pcc.earley import EarleyParser
from ppci.pcc.baselex import EOF


class gen_tokens:
    """ Helper that generates tokens from a list of strings """
    def __init__(self, lst):
        def tokGen():
            loc = SourceLocation('', 0, 0, 0)
            for t in lst:
                if isinstance(t, tuple):
                    t, v = t
                else:
                    t, v = t, t
                yield Token(t, v, loc)
            while True:
                yield Token(EOF, EOF, loc)
        self.tokens = tokGen()
        self.token = self.tokens.__next__()

    def next_token(self):
        t = self.token
        if t.typ != EOF:
            self.token = self.tokens.__next__()
        return t


class LrParserBuilderTestCase(unittest.TestCase):
    """ Test basic LR(1) parser generator constructs """
    def test_simple_grammar(self):
        # 1. define a simple grammar:
        g = Grammar()
        g.add_terminals(['identifier', '(', ')', '+', '*'])
        g.add_production('input', ['expression'])
        g.add_production('expression', ['term'])
        g.add_production('expression', ['expression', '+', 'term'])
        g.add_production('term', ['factor'])
        g.add_production('term', ['term', '*', 'factor'])
        g.add_production('factor', ['(', 'expression', ')'])
        g.add_production('factor', ['identifier'])
        g.start_symbol = 'input'
        # 2. define input:
        tokens = gen_tokens(
            ['identifier', '+', 'identifier', '+', 'identifier'])
        # 3. build parser:
        p = LrParserBuilder(g).generate_parser()
        # 4. feed input:
        p.parse(tokens)

    def test_reduce_reduce_conflict(self):
        """ Check if a reduce-reduce conflict is detected """
        # Define a grammar with an obvious reduce-reduce conflict:
        g = Grammar()
        g.add_terminals(['id'])
        g.add_production('goal', ['a'])
        g.add_production('a', ['b'])
        g.add_production('a', ['c'])
        g.add_production('b', ['id'])
        g.add_production('c', ['id'])
        g.start_symbol = 'goal'
        with self.assertRaises(ParserGenerationException):
            LrParserBuilder(g).generate_parser()

    def test_shift_reduce_conflict(self):
        """ Must be handled automatically by doing shift """
        g = Grammar()
        g.add_terminals([EOF, 'if', 'then', 'else', 'ass'])
        # Ambiguous grammar:
        g.add_production('if_stmt', ['if', 'then', 'stmt'])
        g.add_production('if_stmt', ['if', 'then', 'stmt', 'else', 'stmt'])
        g.add_production('stmt', ['if_stmt'])
        g.add_production('stmt', ['ass'])
        g.start_symbol = 'stmt'
        p = LrParserBuilder(g).generate_parser()
        # Ambiguous program:
        tokens = gen_tokens(['if', 'then', 'if', 'then', 'ass', 'else', 'ass'])
        p.parse(tokens)

    def test_undefined_terminal(self):
        """ Test correct behavior when a terminal is undefined """
        g = Grammar()
        g.add_terminals(['b'])
        g.add_production('goal', ['a'])
        g.add_production('a', ['b'])
        g.add_production('a', ['c'])
        g.start_symbol = 'goal'
        with self.assertRaises(ParserGenerationException):
            LrParserBuilder(g).generate_parser()

    def test_redefine_terminal(self):
        """ Test correct behavior when a terminal is redefined """
        g = Grammar()
        g.add_terminals([EOF, 'b', 'c'])
        g.add_production('goal', ['a'])
        with self.assertRaises(ParserGenerationException):
            g.add_production('b', ['c'])  # Not allowed
        g.add_production('a', ['c'])
        g.start_symbol = 'goal'
        LrParserBuilder(g).generate_parser()

    def test_empty(self):
        """ Test empty token stream """
        g = Grammar()
        g.add_terminals([','])
        g.add_production('input', [','])
        g.start_symbol = 'input'
        p = LrParserBuilder(g).generate_parser()
        tokens = gen_tokens([])
        with self.assertRaises(ParserException):
            p.parse(tokens)

    def test_eps(self):
        """ Test epsilon terminal """
        g = Grammar()
        g.add_terminals(['a', 'b'])
        g.add_production('input', ['optional_a', 'b'])
        g.add_production('optional_a', ['a'])
        g.add_production('optional_a', [])
        g.start_symbol = 'input'
        p = LrParserBuilder(g).generate_parser()
        tokens = gen_tokens(['b'])
        p.parse(tokens)

    def test_eps2(self):
        g = Grammar()
        g.add_terminals(['id', ':'])
        g.add_production('input', ['opt_lab', 'ins', 'op1'])
        g.add_production('input', ['ins', 'op1'])
        g.add_production('opt_lab', ['id', ':'])
        g.add_production('ins', ['id'])
        g.add_production('op1', ['id'])
        g.start_symbol = 'input'
        p = LrParserBuilder(g).generate_parser()
        tokens = gen_tokens(['id', ':', 'id', 'id'])   # i.e. "lab_0: inc rax"
        p.parse(tokens)
        tokens = gen_tokens(['id', 'id'])   # i.e. "inc rax"
        p.parse(tokens)

    def test_eps_sequence(self):
        """ Test epsilon terminal for use in sequences """
        g = Grammar()
        g.add_terminals(['a'])
        g.add_production('aas', [])
        g.add_production('aas', ['aas', 'a'])
        g.start_symbol = 'aas'
        p = LrParserBuilder(g).generate_parser()
        tokens = gen_tokens(['a', 'a', 'a'])
        p.parse(tokens)
        tokens = gen_tokens([])
        p.parse(tokens)

    def test_cb(self):
        """ Test callback of one rule and order or parameters """
        self.cb_called = False

        def cb(a, c, b):
            self.cb_called = True
            self.assertEqual(a.val, 'a')
            self.assertEqual(b.val, 'b')
            self.assertEqual(c.val, 'c')
        g = Grammar()
        g.add_terminals(['a', 'b', 'c'])
        g.add_production('goal', ['a', 'c', 'b'], cb)
        g.start_symbol = 'goal'
        p = LrParserBuilder(g).generate_parser()
        tokens = gen_tokens(['a', 'c', 'b'])
        p.parse(tokens)
        self.assertTrue(self.cb_called)


class GrammarTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print(self, mock_stdout):
        grammar = Grammar()
        grammar.add_terminal('a')
        grammar.add_production('b', ['a', 'a'])
        print_grammar(grammar)
        grammar.dump()
        self.assertTrue(mock_stdout.getvalue())

    def test_redefine_non_terminal(self):
        grammar = Grammar()
        grammar.add_terminal('a')
        self.assertTrue(grammar.is_terminal('a'))
        grammar.add_production('b', ['a', 'a'])
        with self.assertRaises(ParserGenerationException):
            grammar.add_terminal('b')

    def test_rewrite_epsilons(self):
        """ Test grammar rewriting. This involves the removal of epsilon
        rules. """
        grammar = Grammar()
        grammar.add_terminals(['a', 'b', 'c'])
        grammar.add_production('X', [])
        grammar.add_production('X', ['c'])
        grammar.add_production('Y', ['X', 'a'])
        self.assertFalse(grammar.is_normal)
        self.assertEqual(1, len(grammar.productions_for_name('Y')))
        grammar.rewrite_eps_productions()
        self.assertEqual(2, len(grammar.productions_for_name('Y')))
        self.assertTrue(grammar.is_normal)


class ExpressionGrammarTestCase(unittest.TestCase):
    def setUp(self):
        g = Grammar()
        g.add_terminals(['EOF', 'identifier', '(', ')', '+', '*', 'num'])
        g.add_production('input', ['expression'])
        g.add_production('expression', ['term'])
        g.add_production('expression', ['expression', '+', 'term'])
        g.add_production('term', ['factor'])
        g.add_production('term', ['term', '*', 'factor'])
        g.add_production('factor', ['(', 'expression', ')'])
        g.add_production('factor', ['identifier'])
        g.add_production('factor', ['num'])
        g.start_symbol = 'input'
        self.g = g

    def test_first_simple_grammar(self):
        # 1. define a simple grammar:
        first = calculate_first_sets(self.g)
        self.assertEqual(first['input'], {'identifier', '(', 'num'})
        self.assertEqual(first['term'], {'identifier', '(', 'num'})

    def test_canonical(self):
        pb = LrParserBuilder(self.g)
        s0 = pb.initial_item_set()
        s, gt, _ = pb.gen_canonical_set(s0)
        # Must result in 12 sets:
        self.assertEqual(len(s), 24)


class ParserGeneratorTestCase(unittest.TestCase):
    """ Tests several parts of the parser generator """
    def setUp(self):
        g = Grammar()
        g.add_terminals(['(', ')'])
        g.add_production('goal', ['list'])
        g.add_production('list', ['list', 'pair'])
        g.add_production('list', ['pair'])
        g.add_production('pair', ['(', 'pair', ')'])
        g.add_production('pair', ['(', ')'])
        g.start_symbol = 'goal'
        self.g = g

    def test_first_set(self):
        pb = LrParserBuilder(self.g)
        for a in ['(', ')', EOF, 'EPS']:
            self.assertEqual(pb.first[a], {a})
        for nt in ['list', 'pair', 'goal']:
            self.assertEqual(pb.first[nt], {'('})

    def test_init_item_set(self):
        p0, p1, p2, p3, p4 = self.g.productions
        s0 = LrParserBuilder(self.g).initial_item_set()
        self.assertEqual(len(s0), 9)    # 9 with the goal rule included!
        self.assertIn(Item(p0, 0, EOF), s0)
        self.assertIn(Item(p1, 0, EOF), s0)
        self.assertIn(Item(p1, 0, '('), s0)
        self.assertIn(Item(p2, 0, EOF), s0)
        self.assertIn(Item(p2, 0, '('), s0)
        self.assertIn(Item(p3, 0, EOF), s0)
        self.assertIn(Item(p3, 0, '('), s0)
        self.assertIn(Item(p4, 0, EOF), s0)
        self.assertIn(Item(p4, 0, '('), s0)

    def test_canonical(self):
        pb = LrParserBuilder(self.g)
        s0 = pb.initial_item_set()
        s, gt, _ = pb.gen_canonical_set(s0)
        # Must result in 12 sets:
        self.assertEqual(len(s), 12)

    def test_closure(self):
        p0, p1, p2, p3, p4 = self.g.productions
        s0 = set()
        s0.add(Item(p0, 0, EOF))
        self.assertEqual(len(s0), 1)    # 1 rule
        self.assertIn(Item(p0, 0, EOF), s0)

        # Invoke closure on set:
        s0 = LrParserBuilder(self.g).closure(s0)
        self.assertIn(Item(p0, 0, EOF), s0)
        self.assertIn(Item(p1, 0, EOF), s0)
        self.assertIn(Item(p1, 0, '('), s0)
        self.assertIn(Item(p2, 0, EOF), s0)
        self.assertIn(Item(p2, 0, '('), s0)
        self.assertIn(Item(p3, 0, EOF), s0)
        self.assertIn(Item(p3, 0, '('), s0)
        self.assertIn(Item(p4, 0, EOF), s0)
        self.assertIn(Item(p4, 0, '('), s0)

    def test_parser(self):
        tokens = ['(', '(', ')', ')', '(', ')']
        # 3. build parser:
        p = LrParserBuilder(self.g).generate_parser()
        self.assertEqual(len(p.goto_table), 5)
        self.assertEqual(len(p.action_table), 19)

        # 4. feed input:
        p.parse(gen_tokens(tokens))


class EarleyParserTestCase(unittest.TestCase):
    def test_expression_grammar(self):
        grammar = Grammar()
        grammar.add_terminals(
            ['EOF', 'identifier', '(', ')', '+', '*', 'num'])
        grammar.add_production(
            'input', ['expression'], lambda rhs: rhs)
        grammar.add_production(
            'expression', ['term'], lambda rhs: rhs)
        grammar.add_production(
            'expression', ['expression', '+', 'term'],
            lambda rh1, rh2, rh3: rh1 + rh3)
        grammar.add_production('term', ['factor'], lambda rhs: rhs)
        grammar.add_production(
            'term', ['term', '*', 'factor'], lambda rh1, rh2, rh3: rh1 * rh3)
        grammar.add_production(
            'factor', ['(', 'expression', ')'], lambda rh1, rh2, rh3: rh2)
        grammar.add_production('factor', ['identifier'])
        grammar.add_production('factor', ['num'], lambda rhs: rhs.val)
        grammar.start_symbol = 'input'
        parser = EarleyParser(grammar)
        result = parser.parse(gen_tokens(
            [('num', 7), '*', ('num', 11), '+', ('num', 3)]))
        self.assertEqual(80, result)

    def test_ambiguous_grammar(self):
        """
            Test if ambiguous grammar is handled correctly by priorities
        """
        # TODO: check that ambiguous grammars have different priorities!
        grammar = Grammar()
        grammar.add_terminals(['mov', 'num', '+'])
        grammar.add_production(
            'expr', ['num', '+', 'num'],
            lambda rh1, _, rh3: rh1.val + rh3.val,
            priority=3)
        grammar.add_production(
            'expr', ['num', '+', 'num'],
            lambda rh1, _, rh3: rh1.val + rh3.val + 1,
            priority=2)
        grammar.add_production(
            'ins', ['mov', 'expr'],
            lambda _, rh2: rh2,
            priority=2)
        grammar.start_symbol = 'ins'
        parser = EarleyParser(grammar)
        result = parser.parse(gen_tokens(['mov', ('num', 1), '+', ('num', 1)]))
        self.assertEqual(3, result)

    def test_cb(self):
        """ Test callback of one rule and order or parameters """
        self.cb_called = False

        def cb(a, c, b):
            self.cb_called = True
            self.assertEqual(a.val, 'a')
            self.assertEqual(b.val, 'b')
            self.assertEqual(c.val, 'c')
        g = Grammar()
        g.add_terminals(['a', 'b', 'c'])
        g.add_production('goal', ['a', 'c', 'b'], cb)
        g.start_symbol = 'goal'
        p = EarleyParser(g)
        tokens = gen_tokens(['a', 'c', 'b'])
        p.parse(tokens)
        self.assertTrue(self.cb_called)

    def test_invalid_parse(self):
        """ Check what happens when """
        g = Grammar()
        g.add_terminals(['a', 'b', 'c'])
        g.add_production('goal', ['a', 'c', 'b'])
        g.start_symbol = 'goal'
        p = EarleyParser(g)
        tokens = gen_tokens(['d'])
        with self.assertRaises(CompilerError):
            p.parse(tokens)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_dump_parse(self, mock_stdout):
        """ Test the debug dump of the parser """
        g = Grammar()
        g.add_terminals(['a', 'b', 'c'])
        g.add_production('goal', ['a', 'c', 'b'])
        g.start_symbol = 'goal'
        p = EarleyParser(g)
        tokens = gen_tokens(['a', 'c', 'b'])
        p.parse(tokens, debug_dump=True)


class GrammarParserTestCase(unittest.TestCase):
    def test_load_as_module(self):
        grammar = """
        %tokens a b c
        %%
        res: aa { res = arg1 };
        aa: { res = [] }
          | aa a { arg1.append(arg2.val); res = arg1};
        """
        i = io.StringIO(grammar)
        o = io.StringIO()
        transform(i, o)
        # print(o.getvalue())

        i2 = io.StringIO(grammar)
        mod = load_as_module(i2)
        parser = mod.Parser()
        res = parser.parse(gen_tokens(['a', 'a', 'a']))
        self.assertSequenceEqual(['a', 'a', 'a'], res)

        res = parser.parse(gen_tokens([]))
        self.assertSequenceEqual([], res)

        res = parser.parse(gen_tokens(['a', 'a', 'a', 'a']))
        self.assertSequenceEqual(['a', 'a', 'a', 'a'], res)

    def test_load_as_with_header(self):
        grammar = """
        import logging
        %tokens a b c
        %%
        res: aa { return arg1 };
        aa: { return [] }
          | aa a { arg1.append(arg2.val); return arg1};
        """
        i = io.StringIO(grammar)
        o = io.StringIO()
        transform(i, o)


if __name__ == '__main__':
    unittest.main()
