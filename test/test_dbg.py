import io
import unittest
from ppci.arch.example import SimpleTarget
from ppci.binutils.dbg import Debugger, DummyDebugDriver
from ppci.api import c3c
from ppci.api import write_ldb


class DebuggerTestCase(unittest.TestCase):
    def setUp(self):
        self.debugger = Debugger(SimpleTarget(), DummyDebugDriver())

    def test_1(self):
        print(self.debugger)


class LdbFormatTestCase(unittest.TestCase):
    def setUp(self):
        src = """
        module x;
        function int sum(int a, int b)
        {
            var int sum = 0;
            sum = sum + a + b;
            return a +sum+ b + 1234;
        }
        """
        self.obj = c3c([io.StringIO(src)], [], 'arm')

    def test_export_ldb(self):
        """ Check the exporting to ldb format """
        self.assertTrue(self.obj.debug_info.locations)
        output_file = io.StringIO()
        write_ldb(self.obj, output_file)
        self.assertTrue(output_file.getvalue())


if __name__ == '__main__':
    unittest.main()
