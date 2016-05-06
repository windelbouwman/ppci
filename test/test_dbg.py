import io
import unittest
from ppci.common import CompilerError
from ppci.binutils.dbg import Debugger, DummyDebugDriver
from ppci.binutils import debuginfo
from ppci.api import c3c, link, get_arch
from ppci.api import write_ldb


class DebuggerTestCase(unittest.TestCase):
    """ Test the debugger class """
    def setUp(self):
        self.debugger = Debugger(get_arch('arm'), DummyDebugDriver())

    def test_stop(self):
        self.debugger.stop()

    def test_step(self):
        self.debugger.step()

    def test_source_mappings(self):
        src = """
        module x;
        var int Xa;
        function int sum(int a, int b)
        {
            var int sum = 0;
            sum = sum + a + b + Xa;
            return a +sum+ b + 1234;
        }
        """
        obj = c3c([io.StringIO(src)], [], 'arm', debug=True)
        self.debugger.load_symbols(obj)
        self.debugger.find_pc()
        addr = self.debugger.find_address('', 7)
        self.assertTrue(addr is not None)

    def test_expressions_with_globals(self):
        """ See if expressions involving global variables can be evaluated """
        src = """
        module x;
        var int Xa;
        var int[10] B;
        var struct{int g;int f;}[10] C;
        """
        obj = c3c([io.StringIO(src)], [], 'arm', debug=True)
        self.debugger.load_symbols(obj)
        self.assertEqual(0, self.debugger.eval_str('Xa').value)
        self.assertEqual(-9, self.debugger.eval_str('Xa + 1 -10').value)
        self.assertEqual(20, self.debugger.eval_str('(Xa + 1)*20').value)
        with self.assertRaises(CompilerError):
            self.debugger.eval_str('(Xa + 1.2)*"hello"')
        with self.assertRaises(CompilerError):
            self.debugger.eval_str('Baa')
        with self.assertRaises(CompilerError):
            self.debugger.eval_str('B')
        with self.assertRaises(CompilerError):
            self.debugger.eval_str('B.d')
        self.assertEqual(22, self.debugger.eval_str('B[2] + 22').value)
        with self.assertRaises(CompilerError):
            self.debugger.eval_str('C[1]')
        self.assertEqual(32, self.debugger.eval_str('C[2].f + 22+0xA').value)


class DebugFormatTestCase(unittest.TestCase):
    """ Test the internal debug data structures """
    def test_recursive_types(self):
        """ Test how infinite deep type structures such as linked lists
            work out """
        src = """
        module x;
        type struct {
          int payload;
          node_t* next;
        } node_t;
        var node_t* root;
        """
        obj = c3c([io.StringIO(src)], [], 'arm', debug=True)
        # print(obj.debug_info.types)
        debuginfo.serialize(obj.debug_info)
        # print(d)

    def test_export_ldb(self):
        """ Check the exporting to ldb format """
        src = """
        module x;
        var int Xa;
        function int sum(int a, int b)
        {
            var int sum = 0;
            sum = sum + a + b + Xa;
            return a +sum+ b + 1234;
        }
        """
        obj = c3c([io.StringIO(src)], [], 'arm', debug=True)
        self.assertTrue(obj.debug_info.locations)
        self.assertTrue(obj.debug_info.functions)
        self.assertTrue(obj.debug_info.variables)
        output_file = io.StringIO()
        write_ldb(obj, output_file)
        self.assertTrue(output_file.getvalue())


class LinkWithDebugTestCase(unittest.TestCase):
    def test_two_files(self):
        src1 = """
        module x;
        var int Xa;
        function int sum(int a, int b)
        {
            var int sum = 0;
            sum = sum + a + b + Xa;
            return a +sum+ b + 1234;
        }
        """
        src2 = """
        module y;
        var int Xa;
        function int sum(int a, int b)
        {
            var int sum = 0;
            sum = sum + a + b + Xa;
            return a +sum+ b + 1234;
        }
        """
        layout = """
            MEMORY rom LOCATION=0x8000 SIZE=0x3000 {
              DEFINESYMBOL(codestart)
              SECTION(code)
              DEFINESYMBOL(codeend)
            }
            MEMORY ram LOCATION=0x2000 SIZE=0x3000 {
              SECTION(data)
            }
        """
        obj1 = c3c([io.StringIO(src1)], [], 'arm', debug=True)
        obj2 = c3c([io.StringIO(src2)], [], 'arm', debug=True)
        obj = link([obj1, obj2], layout=io.StringIO(layout), debug=True)
        self.assertTrue(obj.debug_info.locations)
        self.assertTrue(obj.debug_info.functions)
        self.assertTrue(obj.debug_info.variables)


if __name__ == '__main__':
    unittest.main()
