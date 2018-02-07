import io
import unittest
from unittest.mock import MagicMock, patch
from ppci.common import CompilerError
from ppci.binutils.dbg.debugger import Debugger, TmpValue
from ppci.binutils.dbg.debug_driver import DebugState
from ppci.binutils.dbg.dummy_driver import DummyDebugDriver
from ppci.binutils.dbg.cli import DebugCli
from ppci.binutils.dbg.gdb.client import GdbDebugDriver, decoder
from ppci.binutils.dbg.gdb.transport import Transport
from ppci.binutils import debuginfo
from ppci.binutils.objectfile import ObjectFile
from ppci.api import c3c, link, get_arch
from ppci.api import write_ldb
from ppci.common import SourceLocation


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
        self.debugger_mock.configure_mock(status=DebugState.STOPPED)
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
    def test_readregs(self, mock_stdout):
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
        self.cmd('readregs')
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


class GdbDecoderTestCase(unittest.TestCase):
    def setUp(self):
        self.decoder = decoder()
        next(self.decoder)

    def test_decode_plus(self):
        """ Test that when decoding a + the + is returned """
        msg = self.decoder.send(b'+')
        self.assertEqual('+', msg)
        msg = self.decoder.send(b'+')
        self.assertEqual('+', msg)

    def test_decode_packet(self):
        """ Test that the decoding of a packet """
        msg = self.decoder.send(b'$')
        self.assertEqual(None, msg)
        msg = self.decoder.send(b'a')
        self.assertEqual(None, msg)
        msg = self.decoder.send(b'b')
        self.assertEqual(None, msg)
        msg = self.decoder.send(b'#')
        self.assertEqual(None, msg)
        msg = self.decoder.send(b'2')
        self.assertEqual(None, msg)
        msg = self.decoder.send(b'5')
        self.assertEqual('$ab#25', msg)
        msg = self.decoder.send(b'+')
        self.assertEqual('+', msg)


class TransportMock:
    """ Test dummy to test the GDB protocol """
    def __init__(self):
        self.send_data = bytearray()
        self.response = None

    def send(self, dt):
        self.send_data.extend(dt)
        if self.response:
            data = self.response
            self.response = None
            for byte in data:
                self.on_byte(bytes([byte]))

    def inject(self, data):
        for byte in data:
            self.on_byte(bytes([byte]))


class GdbClientTestCase(unittest.TestCase):
    arch = get_arch('example')

    def setUp(self):
        self.transport_mock = TransportMock()
        self.gdbc = GdbDebugDriver(self.arch, transport=self.transport_mock)
        self.gdbc.status = DebugState.STOPPED

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
        res = self.gdbc.recvpkt()
        self.assertEqual('abc', res)

    def test_send_pkt(self):
        """ Test sending of a single packet """
        self.prepare_response(b'+')
        self.gdbc.sendpkt('s')
        self.check_send(b'$s#73')

    def test_stop(self):
        self.gdbc.status = DebugState.RUNNING
        self.prepare_response(b'$S05#b8')
        self.gdbc.stop()
        self.check_send(b'\x03+')

    def test_step(self):
        """ Test the single step command """
        self.prepare_response(b'+$S05#b8')
        self.gdbc.step()
        self.check_send(b'$s#73+')

    def test_run(self):
        self.prepare_response(b'+')
        self.gdbc.run()
        self.check_send(b'$c#63')

    def test_get_registers(self):
        """ Test reading of registers """
        self.prepare_response(b'+$000000000000000000000000#80')
        regs = self.arch.gdb_registers
        reg_vals = self.gdbc.get_registers(regs)
        self.check_send(b'$g#67+')
        self.assertEqual({reg: 0 for reg in regs}, reg_vals)

    def test_set_breakpoint(self):
        self.prepare_response(b'+$OK#9a')
        self.gdbc.set_breakpoint(98)
        self.check_send(b'$Z0,62,4#7E+')

    def test_clear_breakpoint(self):
        self.prepare_response(b'+$OK#9a')
        self.gdbc.clear_breakpoint(98)
        self.check_send(b'$z0,62,4#9E+')

    def test_read_mem(self):
        """ Test reading of memory """
        self.prepare_response(b'+$01027309#96')
        contents = self.gdbc.read_mem(101, 4)
        self.assertEqual(bytes([1, 2, 0x73, 9]), contents)
        self.check_send(b'$m 65,4#58+')

    def test_write_mem(self):
        """ Test write to memory """
        self.prepare_response(b'+$01027309#96')
        self.gdbc.write_mem(100, bytes([1, 2, 0x73, 9]))
        self.check_send(b'$M 64,4:01027309#07+')

    def prepare_response(self, data):
        """ Prepare mock that we expect this data to be received """
        self.transport_mock.response = data

    def expect_recv(self, data):
        """ Prepare mock that we expect this data to be received """
        self.transport_mock.inject(data)

    def check_send(self, data):
        """ Check that given data was transmitted """
        self.assertEqual(data, self.transport_mock.send_data)


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
