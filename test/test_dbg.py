import unittest
from ppci.arch.example import SimpleTarget
from ppci.binutils.dbg import Debugger, DummyDebugDriver


class DebuggerTestCase(unittest.TestCase):
    def setUp(self):
        self.debugger = Debugger(SimpleTarget(), DummyDebugDriver())

    def test_1(self):
        print(self.debugger)


if __name__ == '__main__':
    unittest.main()
