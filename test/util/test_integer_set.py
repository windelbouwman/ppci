import unittest

from ppci.utils.integer_set import IntegerSet


class IntegerSetTestCase(unittest.TestCase):
    def test_empty(self):
        """ Test the empty set. """
        s = IntegerSet()
        self.assertEqual(s.cardinality(), 0)
        self.assertNotIn(1337, s)
        L = list(s)
        self.assertEqual(L, [])
        self.assertFalse(s)
        self.assertEqual(0, len(s))

    def test_iteration(self):
        """ See how we turn a range set into a list. """
        s = IntegerSet((5, 8), 1)
        L = list(s)
        self.assertEqual(L, [1, 5, 6, 7, 8])

    def test_basics(self):
        """ Test some simple use cases. """
        s = IntegerSet(1, (20, 30), 4, (13, 50))
        self.assertTrue(s)
        self.assertEqual(40, len(s))
        self.assertEqual(s.cardinality(), 40)
        self.assertIn(1, s)
        self.assertNotIn(2, s)
        self.assertNotIn(3, s)
        self.assertIn(4, s)
        self.assertNotIn(5, s)
        self.assertNotIn(6, s)
        self.assertNotIn(12, s)
        self.assertIn(13, s)
        self.assertIn(14, s)
        self.assertIn(50, s)
        self.assertNotIn(51, s)

    def test_equality(self):
        s = IntegerSet(1, 3, 7)
        t = IntegerSet(1, 3, 7)
        u = IntegerSet(1, (3, 7))
        self.assertEqual(s, t)
        self.assertNotEqual(s, u)
        d = {s: 3}
        self.assertEqual(d[t], 3)

    def test_union(self):
        s = IntegerSet(1, 2, 5)
        t = IntegerSet(1, (3, 7))
        self.assertEqual([1, 2, 3, 4, 5, 6, 7], list(s | t))

    def test_difference(self):
        s = IntegerSet((10, 20), 42)
        t = IntegerSet((15, 17))
        u = s - t
        self.assertEqual(u, IntegerSet((10, 14), (18, 20), 42))

    def test_symmetric_difference(self):
        s = IntegerSet((10, 20), 42)
        t = IntegerSet((15, 24))
        u = s ^ t
        self.assertEqual(u, IntegerSet((10, 14), (21, 24), 42))

    def test_intersection(self):
        s = IntegerSet((10, 20), 42)
        t = IntegerSet((15, 22))
        u = s & t
        self.assertEqual(u, IntegerSet((15, 20)))
