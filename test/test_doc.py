import doctest
import unittest


# TODO: make sure pytest finds this:

def load_tests(loader, tests, ignore):
    a = doctest.DocFileSuite('../readme.rst')
    tests.addTests(a)
    return tests


if __name__ == '__main__':
    unittest.main()
