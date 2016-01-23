import unittest
import sys
from ppci.utils.bitfun import rotate_left, rotate_right, BitView


class BitRotationTestCase(unittest.TestCase):
    def test_right_rotation(self):
        self.assertEqual(0xFF000000, rotate_right(0xFF, 8))
        self.assertEqual(0x0FF00000, rotate_right(0xFF, 12))

    def test_left_rotation(self):
        self.assertEqual(0x0000FF00, rotate_left(0xFF, 8))
        self.assertEqual(0x001FE000, rotate_left(0xFF, 13))


class BitViewTestCase(unittest.TestCase):
    """ Checkout the functions of the bit fiddler """
    def test_simple_case(self):
        """ Check the simple case where only one byte is touched """
        dummy_data = bytearray([3, 3, 3, 3])
        bv = BitView(dummy_data, 1, 2)
        bv[4:8] = 5
        self.assertSequenceEqual(bytearray([3, 0x53, 0x3, 3]), dummy_data)

    def test_byte_boundary(self):
        """ Test two bytes """
        dummy_data = bytearray([3, 3, 3, 3])
        bv = BitView(dummy_data, 1, 2)
        bv[4:12] = 0xAB
        self.assertSequenceEqual(bytearray([3, 0xB3, 0xA, 3]), dummy_data)

    def test_large_field(self):
        """ Test three bytes spanning field """
        dummy_data = bytearray([3, 3, 3, 3])
        bv = BitView(dummy_data, 1, 3)
        bv[4:24] = 0xABCDE
        self.assertSequenceEqual(bytearray([3, 0xe3, 0xcd, 0xab]), dummy_data)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
