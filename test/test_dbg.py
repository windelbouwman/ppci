import io
import unittest
from ppci.common import CompilerError
from ppci.binutils.dbg import Debugger, DummyDebugDriver
from ppci.binutils import debuginfo
from ppci.binutils.objectfile import ObjectFile
from ppci.api import c3c, link, get_arch
from ppci.api import write_ldb
from ppci.common import SourceLocation


class DebuggerTestCase(unittest.TestCase):
    """ Test the debugger class """
    arch = get_arch('arm')

    def setUp(self):
        self.debugger = Debugger(self.arch, DummyDebugDriver())

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
        var int* D;
        """
        obj = c3c([io.StringIO(src)], [], self.arch, debug=True)
        self.debugger.load_symbols(obj)
        self.assertEqual(0, self.debugger.eval_c3_str('Xa').value)
        self.assertEqual(-9, self.debugger.eval_c3_str('Xa + 1 -10').value)
        self.assertEqual(20, self.debugger.eval_c3_str('(Xa + 1)*20').value)
        with self.assertRaises(CompilerError):
            self.debugger.eval_c3_str('(Xa + 1.2)*"hello"')
        with self.assertRaises(CompilerError):
            self.debugger.eval_c3_str('Baa')
        with self.assertRaises(CompilerError):
            self.debugger.eval_c3_str('B')
        with self.assertRaises(CompilerError):
            self.debugger.eval_c3_str('B.d')
        self.assertEqual(22, self.debugger.eval_c3_str('B[2] + 22').value)
        with self.assertRaises(CompilerError):
            self.debugger.eval_c3_str('C[1]')
        self.assertEqual(32, self.debugger.eval_c3_str('C[2].f+22+0xA').value)
        self.assertEqual(0, self.debugger.eval_c3_str('D').value)
        self.assertEqual(0, self.debugger.eval_c3_str('*D').value)
        self.debugger.eval_c3_str('&D')
        self.debugger.eval_c3_str('+D')
        self.debugger.eval_c3_str('-D')

    def test_expressions_with_locals(self):
        """ See if expressions involving global variables can be evaluated """
        src = """
        module x;
        var int Xa;
        function int main()
        {
          var int Xa, b;
          Xa = 2;
          b = 2;
          return Xa + b;
        }
        """
        obj = c3c([io.StringIO(src)], [], self.arch, debug=True)
        self.debugger.load_symbols(obj)
        self.assertEqual(0, self.debugger.eval_c3_str('Xa').value)
        self.assertEqual(-9, self.debugger.eval_c3_str('Xa + 1 -10').value)
        self.assertEqual(20, self.debugger.eval_c3_str('(Xa + 1)*20').value)
        self.assertEqual(0, self.debugger.eval_c3_str('b').value)
        self.debugger.current_function()


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
        self.assertEqual(2, len(obj.debug_info.functions))
        self.assertEqual(2, len(obj.debug_info.variables))

    def test_offset_adjustment(self):
        """ Test if offsets are correctly modified when linking debug info """
        arch = get_arch('arm')
        obj1 = ObjectFile(arch)
        obj1.get_section('code', create=True).add_data(bytes(59))
        obj2 = ObjectFile(arch)
        obj2.get_section('code', create=True).add_data(bytes(59))
        obj2.debug_info = debuginfo.DebugInfo()
        loc = SourceLocation('a.txt', 1, 1, 22)
        obj2.debug_info.add(
            debuginfo.DebugLocation(
                loc,
                address=debuginfo.DebugAddress('code', 5)))
        obj = link([obj1, obj2], debug=True)

        # Take into account alignment! So 60 + 5 = 65.
        self.assertEqual(65, obj.debug_info.locations[0].address.offset)


if __name__ == '__main__':
    unittest.main()
