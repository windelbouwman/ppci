

import unittest
import sys
from ppci.bitfun import rotate_left, rotate_right


class BitRotationTestCase(unittest.TestCase):
    def testRightRotation(self):
        self.assertEqual(0xFF000000, rotate_right(0xFF, 8))
        self.assertEqual(0x0FF00000, rotate_right(0xFF, 12))

    def testLeftRotation(self):
        self.assertEqual(0x0000FF00, rotate_left(0xFF, 8))
        self.assertEqual(0x001FE000, rotate_left(0xFF, 13))


if __name__ == '__main__':
    unittest.main()
    sys.exit()
