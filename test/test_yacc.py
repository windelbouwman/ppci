import unittest
import io
from ppci.pyyacc import Grammar, Item, ParserGenerationException
from ppci.pyyacc import ParserException, load_as_module
from ppci.pyyacc import EPS, EOF, calculate_first_sets, transform
from ppci import Token, SourceLocation


class genTokens:
    def __init__(self, lst):
        def tokGen():
            loc = SourceLocation('', 0, 0, 0)
            for t in lst:
                yield Token(t, t, loc)
            while True:
                yield Token(EOF, EOF, loc)
        self.tokens = tokGen()
        self.token = self.tokens.__next__()

    def next_token(self):
        t = self.token
        if t.typ != EOF:
            self.token = self.tokens.__next__()
        return t


class testLR(unittest.TestCase):
    """ Test basic LR(1) parser generator constructs """
    def testSimpleGrammar(self):
        # 1. define a simple grammar:
        g = Grammar(['identifier', '(', ')', '+', '*'])
        g.add_production('input', ['expression'])
        g.add_production('expression', ['term'])
        g.add_production('expression', ['expression', '+', 'term'])
        g.add_production('term', ['factor'])
        g.add_production('term', ['term', '*', 'factor'])
        g.add_production('factor', ['(', 'expression', ')'])
        g.add_production('factor', ['identifier'])
        g.start_symbol = 'input'
        # 2. define input:
        tokens = genTokens(['identifier', '+', 'identifier', '+', 'identifier'])
        # 3. build parser:
        p = g.generate_parser()
        # 4. feed input:
        p.parse(tokens)

    def testReduceReduceConflict(self):
        """ Check if a reduce-reduce conflict is detected """
        # Define a grammar with an obvious reduce-reduce conflict:
        g = Grammar(['id'])
        g.add_production('goal', ['a'])
        g.add_production('a', ['b'])
        g.add_production('a', ['c'])
        g.add_production('b', ['id'])
        g.add_production('c', ['id'])
        g.start_symbol = 'goal'
        with self.assertRaises(ParserGenerationException):
            p = g.generate_parser()

    def testShiftReduceConflict(self):
        """ Must be handled automatically by doing shift """
        g = Grammar([EOF, 'if', 'then', 'else', 'ass'])
        # Ambiguous grammar:
        g.add_production('if_stmt', ['if', 'then', 'stmt'])
        g.add_production('if_stmt', ['if', 'then', 'stmt', 'else', 'stmt'])
        g.add_production('stmt', ['if_stmt'])
        g.add_production('stmt', ['ass'])
        g.start_symbol = 'stmt'
        p = g.generate_parser()
        # Ambiguous program:
        tokens = genTokens(['if', 'then','if', 'then', 'ass', 'else', 'ass'])
        p.parse(tokens)

    def testUndefinedTerminal(self):
        """ Test correct behavior when a terminal is undefined """
        g = Grammar(['b'])
        g.add_production('goal', ['a'])
        g.add_production('a', ['b'])
        g.add_production('a', ['c'])
        g.start_symbol = 'goal'
        with self.assertRaises(ParserGenerationException):
            g.generate_parser()

    def testRedefineTerminal(self):
        """ Test correct behavior when a terminal is redefined """
        g = Grammar([EOF, 'b', 'c'])
        g.add_production('goal', ['a'])
        with self.assertRaises(ParserGenerationException):
            g.add_production('b', ['c']) # Not allowed
        g.add_production('a', ['c'])
        g.start_symbol = 'goal'
        g.generate_parser()

    def testEmpty(self):
        """ Test empty token stream """
        g = Grammar([','])
        g.add_production('input', [','])
        g.start_symbol = 'input'
        p = g.generate_parser()
        tokens = genTokens([])
        with self.assertRaises(ParserException):
            p.parse(tokens)

    def testEps(self):
        """ Test epsilon terminal """
        g = Grammar(['a', 'b'])
        g.add_production('input', ['optional_a', 'b'])
        g.add_production('optional_a', ['a'])
        g.add_production('optional_a', [])
        g.start_symbol = 'input'
        p = g.generate_parser()
        tokens = genTokens(['b'])
        p.parse(tokens)

    def testEps2(self):
        g = Grammar(['id', ':'])
        g.add_production('input', ['opt_lab', 'ins', 'op1'])
        g.add_production('input', ['ins', 'op1'])
        g.add_production('opt_lab', ['id', ':'])
        g.add_production('ins', ['id'])
        g.add_production('op1', ['id'])
        g.start_symbol = 'input'
        p = g.generate_parser()
        tokens = genTokens(['id', ':', 'id', 'id'])   # i.e. "lab_0: inc rax" 
        p.parse(tokens)
        tokens = genTokens(['id', 'id'])   # i.e. "inc rax"
        p.parse(tokens)

    def testEpsSequence(self):
        """ Test epsilon terminal for use in sequences """
        g = Grammar(['a'])
        g.add_production('aas', [])
        g.add_production('aas', ['aas', 'a'])
        g.start_symbol = 'aas'
        p = g.generate_parser()
        tokens = genTokens(['a', 'a', 'a'])
        p.parse(tokens)
        tokens = genTokens([])
        p.parse(tokens)

    def test_cb(self):
        """ Test callback of one rule and order or parameters """
        self.cb_called = False
        def cb(a, c, b):
            self.cb_called = True
            self.assertEqual(a.val, 'a')
            self.assertEqual(b.val, 'b')
            self.assertEqual(c.val, 'c')
        g = Grammar(['a', 'b', 'c'])
        g.add_production('goal', ['a', 'c', 'b'], cb)
        g.start_symbol = 'goal'
        p = g.generate_parser()
        tokens = genTokens(['a', 'c', 'b'])
        p.parse(tokens)
        self.assertTrue(self.cb_called)


class testExpressionGrammar(unittest.TestCase):
    def setUp(self):
        g = Grammar(['EOF', 'identifier', '(', ')', '+', '*', 'num'])
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

    def testFirstSimpleGrammar(self):
        # 1. define a simple grammar:
        first = calculate_first_sets(self.g)
        self.assertEqual(first['input'], {'identifier', '(', 'num'})
        self.assertEqual(first['term'], {'identifier', '(', 'num'})

    def testCanonical(self):
        s0 = self.g.initial_item_set()
        s, gt, _ = self.g.gen_canonical_set(s0)
        # Must result in 12 sets:
        self.assertEqual(len(s), 24)


class testParserGenerator(unittest.TestCase):
    """ Tests several parts of the parser generator """
    def setUp(self):
        g = Grammar(['(', ')'])
        g.add_production('goal', ['list'])
        g.add_production('list', ['list', 'pair'])
        g.add_production('list', ['pair'])
        g.add_production('pair', ['(', 'pair', ')'])
        g.add_production('pair', ['(', ')'])
        g.start_symbol = 'goal'
        self.g = g

    def testFirstSet(self):
        for a in ['(', ')', EOF, 'EPS']:
            self.assertEqual(self.g.first[a], {a})
        for nt in ['list', 'pair', 'goal']:
            self.assertEqual(self.g.first[nt], {'('})

    def testInitItemSet(self):
        p0, p1, p2, p3, p4 = self.g.productions
        s0 = self.g.initial_item_set()
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

    def testCanonical(self):
        s0 = self.g.initial_item_set()
        s, gt, _ = self.g.gen_canonical_set(s0)
        # Must result in 12 sets:
        self.assertEqual(len(s), 12)

    def testClosure(self):
        p0, p1, p2, p3, p4 = self.g.productions
        s0 = set()
        s0.add(Item(p0, 0, EOF))
        self.assertEqual(len(s0), 1)    # 1 rule
        self.assertIn(Item(p0, 0, EOF), s0)

        # Invoke closure on set:
        s0 = self.g.closure(s0)
        self.assertIn(Item(p0, 0, EOF), s0)
        self.assertIn(Item(p1, 0, EOF), s0)
        self.assertIn(Item(p1, 0, '('), s0)
        self.assertIn(Item(p2, 0, EOF), s0)
        self.assertIn(Item(p2, 0, '('), s0)
        self.assertIn(Item(p3, 0, EOF), s0)
        self.assertIn(Item(p3, 0, '('), s0)
        self.assertIn(Item(p4, 0, EOF), s0)
        self.assertIn(Item(p4, 0, '('), s0)

    def testParser(self):
        tokens = ['(', '(', ')', ')', '(', ')']
        # 3. build parser:
        p = self.g.generate_parser()
        self.assertEqual(len(p.goto_table), 5)
        self.assertEqual(len(p.action_table), 19)

        # 4. feed input:
        p.parse(genTokens(tokens))


class testGrammarParser(unittest.TestCase):
    def testLoadAsModule(self):
        grammar = """
        %tokens a b c
        %%
        res: aa { return arg1 };
        aa: { return [] }
          | aa a { arg1.append(arg2.val); return arg1};
        """
        i = io.StringIO(grammar)
        o = io.StringIO()
        transform(i, o)
        # print(o.getvalue())

        i2 = io.StringIO(grammar)
        mod = load_as_module(i2)
        parser = mod.Parser()
        res = parser.parse(genTokens(['a', 'a', 'a']))
        # print(res)
        self.assertSequenceEqual(['a', 'a', 'a'], res)


    def testLoadAsWithHeader(self):
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
