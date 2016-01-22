import unittest
import io
import os
import argparse

from ppci.utils.tree import Tree, from_string
from ppci.codegen import burg

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


if __name__ == '__main__':
    unittest.main()
