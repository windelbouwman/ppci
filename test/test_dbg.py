import unittest
import io
from ppci.arch.example import SimpleTarget
from ppci.dbg import Debugger, DummyDebugDriver


class DebugTestCase(unittest.TestCase):
    def setUp(self):
        self.debugger = Debugger(SimpleTarget(), DummyDebugDriver())

    def test_1(self):
        print(self.debugger)


if __name__ == '__main__':
    unittest.main()
