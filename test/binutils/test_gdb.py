import unittest

from ppci.api import get_arch
from ppci.binutils.dbg.debug_driver import DebugState
from ppci.binutils.dbg.gdb.client import GdbDebugDriver
from ppci.binutils.dbg.gdb.rsp import decoder, RspHandler


class GdbDecoderTestCase(unittest.TestCase):
    def setUp(self):
        self.decoder = decoder()
        next(self.decoder)

    def test_decode_plus(self):
        """Test that when decoding a + the + is returned"""
        msg = self.decoder.send(b"+")
        self.assertEqual("+", msg)
        msg = self.decoder.send(b"+")
        self.assertEqual("+", msg)

    def test_decode_packet(self):
        """Test that the decoding of a packet"""
        msg = self.decoder.send(b"$")
        self.assertEqual(None, msg)
        msg = self.decoder.send(b"a")
        self.assertEqual(None, msg)
        msg = self.decoder.send(b"b")
        self.assertEqual(None, msg)
        msg = self.decoder.send(b"#")
        self.assertEqual(None, msg)
        msg = self.decoder.send(b"2")
        self.assertEqual(None, msg)
        msg = self.decoder.send(b"5")
        self.assertEqual("$ab#25", msg)
        msg = self.decoder.send(b"+")
        self.assertEqual("+", msg)


class RspTestCase(unittest.TestCase):
    def test_rsp_pack(self):
        data = "abc"
        res = RspHandler.rsp_pack(data)
        self.assertEqual("$abc#26", res)

    def test_rsp_unpack(self):
        pkt = "$abc#26"
        res = RspHandler.rsp_unpack(pkt)
        self.assertEqual("abc", res)

    def test_rsp_unpack_invalid_crc(self):
        pkt = "$abc#20"
        with self.assertRaises(ValueError):
            RspHandler.rsp_unpack(pkt)

    def test_rsp_unpack_invalid_packet(self):
        pkt = "a"
        with self.assertRaises(ValueError):
            RspHandler.rsp_unpack(pkt)


class TransportMock:
    """Test dummy to test the GDB protocol"""

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
    arch = get_arch("example")

    def setUp(self):
        self.transport_mock = TransportMock()
        self.gdbc = GdbDebugDriver(self.arch, transport=self.transport_mock)
        self.gdbc.status = DebugState.STOPPED

    def test_read_pkt(self):
        """Test reading of a pkt"""
        self.expect_recv(b"zzz$abc#26hhh")
        res = self.gdbc._recv_message()
        self.assertEqual("abc", res)

    def test_send_pkt(self):
        """Test sending of a single packet"""
        self.prepare_response(b"+")
        self.gdbc._send_message("s")
        self.check_send(b"$s#73")

    def test_stop(self):
        self.gdbc.status = DebugState.RUNNING
        self.prepare_response(b"$S05#b8")
        self.gdbc.stop()
        self.check_send(b"\x03+")

    def test_step(self):
        """Test the single step command"""
        self.prepare_response(b"+$S05#b8")
        self.gdbc.step()
        self.check_send(b"$s#73+")

    def test_run(self):
        self.prepare_response(b"+")
        self.gdbc.run()
        self.check_send(b"$c#63")

    def test_get_registers(self):
        """Test reading of registers"""
        self.prepare_response(b"+$000000000000000000000000#80")
        regs = self.arch.gdb_registers
        reg_vals = self.gdbc.get_registers(regs)
        self.check_send(b"$g#67+")
        self.assertEqual(dict.fromkeys(regs, 0), reg_vals)

    def test_set_breakpoint(self):
        self.prepare_response(b"+$OK#9a")
        self.gdbc.set_breakpoint(98)
        self.check_send(b"$Z0,62,4#7E+")

    def test_clear_breakpoint(self):
        self.prepare_response(b"+$OK#9a")
        self.gdbc.clear_breakpoint(98)
        self.check_send(b"$z0,62,4#9E+")

    def test_read_mem(self):
        """Test reading of memory"""
        self.prepare_response(b"+$01027309#96")
        contents = self.gdbc.read_mem(101, 4)
        self.assertEqual(bytes([1, 2, 0x73, 9]), contents)
        self.check_send(b"$m 65,4#58+")

    def test_write_mem(self):
        """Test write to memory"""
        self.prepare_response(b"+$01027309#96")
        self.gdbc.write_mem(100, bytes([1, 2, 0x73, 9]))
        self.check_send(b"$M 64,4:01027309#07+")

    def prepare_response(self, data):
        """Prepare mock that we expect this data to be received"""
        self.transport_mock.response = data

    def expect_recv(self, data):
        """Prepare mock that we expect this data to be received"""
        self.transport_mock.inject(data)

    def check_send(self, data):
        """Check that given data was transmitted"""
        self.assertEqual(data, self.transport_mock.send_data)


if __name__ == "__main__":
    unittest.main()
