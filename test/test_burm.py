import unittest
import io
import os
import argparse

from ppci.utils.tree import Tree, from_string
from ppci.codegen import burg
from ppci.codegen.burg import BurgSystem
from ppci.codegen.instructionselector import TreeSelector

brg_file = os.path.join(os.path.dirname(__file__), 'data', 'sample4.brg')


class BurgTestCase(unittest.TestCase):
    def test_sample4(self):
        """ Test sample4 burg system, from the fraser paper """
        # Generate matcher from spec:
        buf = io.StringIO()
        args = argparse.Namespace(source=open(brg_file), output=buf)
        burg.main(args)

        # Execute generated script into global scope:
        exec(buf.getvalue(), globals())

        # Sample tree:
        t = Tree('ASGNI',
             Tree('ADDRLP'),
             Tree('ADDI',
                  Tree('CVCI', Tree('INDIRC', Tree('ADDRLP'))),
                  Tree('CNSTI')
                 )
            )

        # Subclass generated matcher:
        class MyMatcher(Matcher):
            def __init__(self):
                super().__init__()
                self.trace = []

            def tr(self, r):
                self.trace.append(r)

        # Match tree:
        mm = MyMatcher()
        mm.gen(t)
        self.assertSequenceEqual([8, 8, 4, 11, 9, 3, 1], mm.trace)


class TreeTestCase(unittest.TestCase):
    def test_structural_equal(self):
        """ Check for equalness of trees """
        t1 = Tree('MOV', Tree('ADD', Tree('reg'), Tree('reg')), Tree('reg'))
        t2 = Tree('MOV', Tree('ADD', Tree('reg'), Tree('reg')), Tree('reg'))
        self.assertTrue(t1.structural_equal(t2))
        self.assertTrue(t2.structural_equal(t1))

    def test_structural_unequal(self):
        """ Check if unequal is detected """
        t1 = Tree('MOV', Tree('ADD', Tree('reg'), Tree('reg')), Tree('reg'))
        t2 = Tree('MOV2', Tree('ADD', Tree('reg'), Tree('reg')), Tree('reg'))
        t3 = Tree('MOV', Tree('ADD', Tree('reg'), Tree('reg')))
        self.assertFalse(t1.structural_equal(t2))
        self.assertFalse(t1.structural_equal(t3))

    def test_fromstring(self):
        """ Check parsing from string """
        t1 = from_string('MOV(ADD(reg,reg),reg)')
        t2 = Tree('MOV', Tree('ADD', Tree('reg'), Tree('reg')), Tree('reg'))
        self.assertTrue(t1.structural_equal(t2))


class TreeMatchingTestCase(unittest.TestCase):
    def test_simple_match(self):
        """ Test if instruction selection on trees works fine """
        class Ctx:
            pass
        context = Ctx()
        tree = Tree('ADD', Tree('VAL', value=1), Tree('VAL', value=2))
        system = BurgSystem()
        for terminal in ['ADD', 'VAL']:
            system.add_terminal(terminal)
        system.add_rule(
            'stm',
            Tree('ADD', Tree('val'), Tree('val')),
            1,
            None,
            lambda ctx, tree, c0, c1: (c0, '+', c1))
        system.add_rule(
            'val',
            Tree('VAL'),
            1,
            None,
            lambda ctx, tree: tree.value)
        system.check()
        selector = TreeSelector(system)
        v = selector.gen(context, tree)
        self.assertEqual((1, '+', 2), v)

    def test_chain_rule(self):
        """ See if multiple chained rules work nicely """
        class Ctx:
            pass
        context = Ctx()
        tree = Tree('ADD', Tree('VAL', value=1), Tree('VAL', value=2))
        system = BurgSystem()
        for terminal in ['ADD', 'VAL']:
            system.add_terminal(terminal)
        system.add_rule(
            'stm',
            Tree('ADD', Tree('expr'), Tree('expr')),
            1,
            None,
            lambda ctx, tree, c0, c1: (c0, '+', c1))
        system.add_rule(
            'expr',
            Tree('val'),
            0,
            None,
            lambda ctx, tree, c0: c0)
        system.add_rule(
            'val',
            Tree('ival'),
            0,
            None,
            lambda ctx, tree, c0: c0)
        system.add_rule(
            'ival',
            Tree('VAL'),
            1,
            None,
            lambda ctx, tree: tree.value)
        system.check()
        selector = TreeSelector(system)
        v = selector.gen(context, tree)
        self.assertEqual((1, '+', 2), v)


if __name__ == '__main__':
    unittest.main()
