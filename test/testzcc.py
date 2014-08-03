import unittest
import os

from ppci.target import target_list

# Store testdir for safe switch back to directory:
testdir = os.path.dirname(os.path.abspath(__file__))

def relpath(*args):
    return os.path.join(testdir, *args)


if __name__ == '__main__':
    unittest.main()
