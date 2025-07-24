import os
import unittest

from ppci.lang.c.castxml import CastXmlReader


testdir = os.path.dirname(os.path.abspath(__file__))


def relpath(*args):
    return os.path.normpath(os.path.join(testdir, *args))


class CastXmlTestCase(unittest.TestCase):
    """Try out cast xml parsing."""

    def test_test8(self):
        reader = CastXmlReader()
        reader.process(relpath("..", "..", "data", "c", "test8.xml"))


if __name__ == "__main__":
    unittest.main()
