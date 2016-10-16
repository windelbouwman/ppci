import io
import unittest
from ppci.common import CompilerError
from ppci.binutils.dbg import Debugger, DummyDebugDriver, TmpValue
from ppci.binutils.dbg_cli import DebugCli
from ppci.binutils.dbg_gdb_client import GdbDebugDriver
from ppci.binutils import debuginfo
from ppci.binutils.objectfile import ObjectFile
from ppci.api import c3c, link, get_arch
from ppci.api import write_ldb
from ppci.common import SourceLocation

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch


class DebuggerTestCase(unittest.TestCase):
    """ Test the debugger class """
    arch = get_arch('arm')

    @classmethod
    def setUpClass(cls):
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
        cls.obj = c3c([io.StringIO(src)], [], 'arm', debug=True)

    def setUp(self):
        self.debugger = Debugger(self.arch, DummyDebugDriver())

    def test_repr(self):
        str(self.debugger)

    def test_run(self):
        self.debugger.run()

    def test_stop(self):
        self.debugger.stop()

    def test_step(self):
        self.debugger.step()

    def test_restart(self):
        self.debugger.restart()

    def test_breakpoint(self):
        self.debugger.load_symbols(self.obj)
        self.debugger.set_breakpoint('', 7)
        self.debugger.clear_breakpoint('', 7)

    def test_non_existing_breakpoint(self):
        self.debugger.load_symbols(self.obj)
        self.debugger.set_breakpoint('', 777)
        self.debugger.clear_breakpoint('', 799)

    def test_load_obj_without_dbg(self):
        obj = ObjectFile(self.arch)
        self.debugger.load_symbols(obj)

    def test_breakpoints(self):
        self.debugger.load_symbols(self.obj)
        self.debugger.get_possible_breakpoints('')

    def test_write_mem(self):
        self.debugger.write_mem(100, bytes([1, 2, 3, 4]))

    def test_disasm(self):
        self.debugger.get_disasm()

    def test_source_mappings(self):
        self.debugger.load_symbols(self.obj)
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
        """ See if expressions involving local variables can be evaluated """
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


class DebugCliTestCase(unittest.TestCase):
    """ Test the command line interface for the debugger """
    def setUp(self):
        self.debugger_mock = MagicMock()
        self.cli = DebugCli(self.debugger_mock)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_info(self, mock_stdout):
        self.debugger_mock.configure_mock(status=0)
        self.cmd('info')

    def test_run(self):
        self.cmd('run')
        self.debugger_mock.run.assert_called_with()

    def test_step(self):
        self.cmd('step')
        self.debugger_mock.step.assert_called_with()

    def test_stop(self):
        self.cmd('stop')
        self.debugger_mock.stop.assert_called_with()

    def test_restart(self):
        self.cmd('restart')
        self.debugger_mock.restart.assert_called_with()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_read(self, mock_stdout):
        """ Test the read functionality """
        self.debugger_mock.read_mem = MagicMock(return_value=bytes(16))
        self.cmd('read 100, 16')
        self.debugger_mock.read_mem.assert_called_with(100, 16)

    def test_write(self):
        self.cmd('write 100, aabbccdd')
        self.debugger_mock.write_mem.assert_called_with(
            100, bytes([0xaa, 0xbb, 0xcc, 0xdd]))

    def test_setbrk(self):
        """ Test set of breakpoint """
        self.cmd('setbrk main.c, 3')
        self.debugger_mock.set_breakpoint.assert_called_with('main.c', 3)

    def test_clrbrk(self):
        """ Test clear breakpoint """
        self.cmd('clrbrk main.c, 3')
        self.debugger_mock.clear_breakpoint.assert_called_with('main.c', 3)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_regs(self, mock_stdout):
        """ Test read registers """
        arch = get_arch('arm')
        r1, r2 = arch.gdb_registers[1:3]
        reg_values = {
            r1: 1,
            r2: 1000,
            }
        self.debugger_mock.get_registers = MagicMock(
            return_value=[r1, r2])
        self.debugger_mock.get_register_values = MagicMock(
            return_value=reg_values)
        self.cmd('regs')
        lines = [
            '   R1 : 0x00000001',
            '   R2 : 0x000003E8',
            ''
        ]
        self.assertEqual('\n'.join(lines), mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_disasm(self, mock_stdout):
        """ Test disassembly commands """
        self.cmd('disasm')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print(self, mock_stdout):
        tmp = TmpValue(1, False, 'uint8')
        self.debugger_mock.eval_c3_str = MagicMock(return_value=tmp)
        self.cmd('print 2+1')
        self.assertIn('=', mock_stdout.getvalue())

    def cmd(self, cmd):
        self.cli.onecmd(cmd)


# @patch('ppci.binutils.dbg_gdb_client.select')
# @patch('select.select')
class GdbClientTestCase(unittest.TestCase):
    arch = get_arch('example')

    def setUp(self):
        with patch('ppci.binutils.dbg_gdb_client.socket.socket'):
            self.gdbc = GdbDebugDriver(self.arch)
        self.sock_mock = self.gdbc.sock
        self.send_data = bytearray()

        def my_send(dt):
            self.send_data.extend(dt)
        self.sock_mock.configure_mock(send=my_send)

    def test_rsp_pack(self):
        data = 'abc'
        res = self.gdbc.rsp_pack(data)
        self.assertEqual('$abc#26', res)

    def test_rsp_unpack(self):
        pkt = '$abc#26'
        res = self.gdbc.rsp_unpack(pkt)
        self.assertEqual('abc', res)

    def test_rsp_unpack_invalid_crc(self):
        pkt = '$abc#20'
        with self.assertRaises(ValueError):
            self.gdbc.rsp_unpack(pkt)

    def test_rsp_unpack_invalid_packet(self):
        pkt = 'a'
        with self.assertRaises(ValueError):
            self.gdbc.rsp_unpack(pkt)

    def test_read_pkt(self):
        """ Test reading of a pkt """
        self.expect_recv(b'zzz$abc#26hhh')
        res = self.gdbc.readpkt()
        self.assertEqual('abc', res)

    @patch('select.select')
    def test_send_pkt(self, select_mock):
        """ Test sending of a single packet """
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+')
        self.gdbc.sendpkt('s')
        self.check_send(b'$s#73')

    @patch('select.select')
    def test_stop(self, select_mock):
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'$S05#b8')
        self.gdbc.stop()
        self.check_send(b'\x03+')

    @patch('select.select')
    def test_step(self, select_mock):
        """ Test the single step command """
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$S05#b8')
        self.gdbc.step()
        self.check_send(b'$s#73+')

    @unittest.skip('todo')
    def test_run(self):
        self.gdbc.run()

    @patch('select.select')
    def test_get_registers(self, select_mock):
        """ Test reading of registers """
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$000000000000000000000000#80')
        regs = self.arch.gdb_registers
        reg_vals = self.gdbc.get_registers(regs)
        self.check_send(b'$g#67+')
        self.assertEqual({reg: 0 for reg in regs}, reg_vals)

    @patch('select.select')
    def test_set_breakpoint(self, select_mock):
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$OK#9a')
        self.gdbc.set_breakpoint(98)
        self.check_send(b'$Z0,62,4#7E+')

    @patch('select.select')
    def test_clear_breakpoint(self, select_mock):
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$OK#9a')
        self.gdbc.clear_breakpoint(98)
        self.check_send(b'$z0,62,4#9E+')

    @patch('select.select')
    def test_read_mem(self, select_mock):
        """ Test reading of memory """
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$01027309#96')
        contents = self.gdbc.read_mem(101, 4)
        self.assertEqual(bytes([1, 2, 0x73, 9]), contents)
        self.check_send(b'$m 65,4#58+')

    @patch('select.select')
    def test_write_mem(self, select_mock):
        """ Test write to memory """
        select_mock.side_effect = [(0, 0, 0)]
        self.expect_recv(b'+$01027309#96')
        self.gdbc.write_mem(100, bytes([1, 2, 0x73, 9]))
        self.check_send(b'$M 64,4:01027309#07')

    def expect_recv(self, data):
        recv = make_recv(data)
        self.sock_mock.configure_mock(recv=recv)

    def check_send(self, data):
        self.assertEqual(data, self.send_data)


def make_recv(data):
    def loop():
        for d in data:
            yield d
    lp = loop()

    def recv(i):
        a = bytearray()
        for _ in range(i):
            nxt = lp.__next__()
            a.append(nxt)
        return bytes(a)
    return recv


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
