""" Test architecture related classes """


import unittest
from ppci.arch.stack import Frame, FramePointerLocation


class FrameTestCase(unittest.TestCase):
    """ Test the stack frame """
    def test_fp_at_top_alignment(self):
        frame = Frame('test', fp_location=FramePointerLocation.TOP)
        location = frame.alloc(5, 4)
        self.assertEqual(-8, location.offset)
        self.assertEqual(8, frame.stacksize)

    def test_fp_at_bottom_alignment(self):
        frame = Frame('test', fp_location=FramePointerLocation.BOTTOM)
        location = frame.alloc(5, 4)
        self.assertEqual(0, location.offset)
        self.assertEqual(5, frame.stacksize)


if __name__ == '__main__':
    unittest.main()
