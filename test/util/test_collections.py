#!/usr/bin/python

import unittest
from ppci.utils.collections import OrderedSet


class OrderedSetTestCase(unittest.TestCase):
    """ Test if graph works.
        - Add nodes
        - add edges
        - mask and unmask nodes
        - combine nodes.
    """
    def test_example(self):
        """ Test example from Raymond (slightly modified) """
        s = OrderedSet('abracadabra')
        t = OrderedSet('simsalabim')
        self.assertSequenceEqual('abrcdsiml', list(s | t))
        self.assertSequenceEqual('ab', list(s & t))
        self.assertSequenceEqual('rcd', list(s - t))

    def test_indexing(self):
        s = OrderedSet('abracadabra')
        self.assertEqual(s[0], 'a')
        self.assertEqual(s[1], 'b')
        s -= {'b'}
        self.assertEqual(s[1], 'r')
