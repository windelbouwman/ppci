import unittest

from ppci.utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ppci.utils.leb128 import signed_leb128_decode, unsigned_leb128_decode


class Leb128TestCase(unittest.TestCase):
    """ Test examples from https://en.wikipedia.org/wiki/LEB128 """
    def test_unsigned_wiki_example(self):
        """ Test the wikipedia example """
        data = unsigned_leb128_encode(624485)
        self.assertEqual(bytes([0xe5, 0x8e, 0x26]), data)
        self.assertEqual(624485, unsigned_leb128_decode(iter(data)))

    def test_signed_wiki_example(self):
        """ Test wikipedia example """
        data = signed_leb128_encode(-624485)
        self.assertEqual(bytes([0x9b, 0xf1, 0x59]), data)
        self.assertEqual(-624485, signed_leb128_decode(iter(data)))

    def test_unsigned_cases(self):
        test_cases = (
            (0, [0x0]),
            (42, [42]),
            (127, [0x7f]),
            (128, [0x80, 1]),
            (255, [0xff, 1]),
            (0xffff, [0xff, 0xff, 0b11]),
        )
        for value, data in test_cases:
            expected_data = bytes(data)
            encoded_data = unsigned_leb128_encode(value)
            self.assertEqual(expected_data, encoded_data)
            decoded_value = unsigned_leb128_decode(iter(expected_data))
            self.assertEqual(value, decoded_value)

    def test_signed_cases(self):
        test_cases = (
            (-64, [0x40]),
            (2, [0x02]),
            (-2, [0x7e]),
            (127, [0xff, 0x00]),
            (-127, [0x81, 0x7f]),
            (128, [0x80, 0x01]),
            (-128, [0x80, 0x7f]),
            (129, [0x81, 0x01]),
            (-129, [0xff, 0x7e]),
        )
        for value, data in test_cases:
            expected_data = bytes(data)
            encoded_data = signed_leb128_encode(value)
            self.assertEqual(expected_data, encoded_data)
            decoded_value = signed_leb128_decode(iter(expected_data))
            self.assertEqual(value, decoded_value)

    def test_unsigned_range(self):
        for x in range(0, 1000):
            data = signed_leb128_encode(x)
            y = signed_leb128_decode(iter(data))
            self.assertEqual(x, y)

    def test_signed_range(self):
        for x in range(-1000, 1000):
            data = signed_leb128_encode(x)
            y = signed_leb128_decode(iter(data))
            self.assertEqual(x, y)