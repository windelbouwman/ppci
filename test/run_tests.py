import sys
import unittest
import os

if sys.version_info.major < 3:
    print('Requires python 3 at least')
    sys.exit()


path_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, path_dir)

loader = unittest.TestLoader()
suite = unittest.TestSuite()

for test in loader.discover('.'):
    suite.addTest(test)

unittest.TextTestRunner().run(suite)

