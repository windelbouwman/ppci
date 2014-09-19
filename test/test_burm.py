import unittest
import io
import os
import argparse

from ppci.tree import Tree
from ppci import pyburg

brg_file = os.path.join(os.path.dirname(__file__), 'data', 'sample4.brg')

class testBURG(unittest.TestCase):
    def testSample4(self):
        """ Test sample4 burg system, from the fraser paper """
        # Generate matcher from spec:
        buf = io.StringIO()
        args = argparse.Namespace(source=open(brg_file), output=buf)
        pyburg.main(args)

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
        self.assertSequenceEqual([8,8,4,11,9,3,1], mm.trace)


if __name__ == '__main__':
    unittest.main()
