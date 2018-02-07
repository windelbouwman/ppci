"""
    Gdb debug client implementation for the debugger driver.
"""

import abc
import binascii
import logging
import struct
import string
from queue import Queue
from ..debug_driver import DebugDriver, DebugState

INTERRUPT = 2
BRKPOINT = 5


class GdbCommHandler(metaclass=abc.ABCMeta):
    """ This class deals with the logic of communication """
    def shake(self, message):
        pass


class ThreadedCommHandler(GdbCommHandler):
    """ A comm handler that uses a thread """
    def __init__(self):
        self.rxqueue = Queue()

    def send(self):
        pass

    def recv(self):
        self.rxqueue.get()


# Idea: the gdb class should work threaded and non-threaded. How to do it?
# class AsyncCommHandler(GdbCommHandler):
#    """ Communicate using asyncio """
#    def __init__(self):
#        self.event_loop = None
#
#    def recv_loop(self):
#        while True:
#            data = await recv()
#
#    def recv(self):
#        if queue:
#            pass
#        else:
#            yield to ioloop


def decoder():
    """ Process a single byte. Keep track of the packet.

    Task of this function is to recognize packets in the form of:
      $foo-bar#00
    or
      +

    This function is a generator object which can be paused in the middle.
    """
    logger = logging.getLogger('decoder')
    byte = yield  # Fetch first byte
    while True:
        if byte == b'$':
            res = bytearray()
            res.extend(byte)
            while True:
                byte = yield
                res.extend(byte)
                if res[-1] == ord('#') and res[-2] != ord("'"):
                    byte = yield
                    res.extend(byte)
                    byte = yield
                    res.extend(byte)
                    byte = yield res.decode('ascii')
                    break
        elif byte == b'+':
            byte = yield byte.decode('ascii')
        else:
            if not isinstance(byte, bytes):
                raise TypeError('Expected byte, got{}'.format(byte))
            logger.info('skipping {}'.format(byte))
            byte = yield


class GdbDebugDriver(DebugDriver):
    """ Implement debugging via the GDB remote interface.

    GDB servers can communicate via the RSP protocol.

    Helpfull resources:

    http://www.embecosm.com/appnotes/ean4/
        embecosm-howto-rsp-server-ean4-issue-2.html

    - https://sourceware.org/gdb/onlinedocs/gdb/Stop-Reply-Packets.html

    Tried to make this class about the protocol itself, not about the
    sending and receiving of bytes. The protocol must be able to
    work using sockets and threads, serial port and threads and asyncio
    sockets.
    """
    logger = logging.getLogger('gdbclient')

    def __init__(self, arch, transport, pcresval=0, swbrkpt=False):
        super().__init__()
        self.arch = arch
        self.transport = transport
        self.status = DebugState.RUNNING
        self.pcresval = pcresval
        self.pcstopval = None
        self._register_values = {}  # Cached map of register values
        self.swbrkpt = swbrkpt
        self.stopreason = INTERRUPT
        self.transport.on_byte = self.process_byte
        self.rxqueue = Queue()
        self.packet_decoder = decoder()
        next(self.packet_decoder)  # Bump decoder to first byte.

    def connect(self):
        self.transport.connect()

    def disconnect(self):
        self.transport.disconnect()

    def __str__(self):
        return 'Gdb debug driver via {}'.format(self.transport)

    @staticmethod
    def rsp_pack(data):
        """ formats data into a RSP packet """
        for a, b in [(x, chr(ord(x) ^ 0x20)) for x in ('}', '*', '#', '$')]:
            data = data.replace(a, '}%s' % b)
        crc = (sum(ord(c) for c in data) % 256)
        return "$%s#%02X" % (data, crc)

    @staticmethod
    def rsp_unpack(pkt):
        """ unpacks an RSP packet, returns the data """
        if pkt[0] != '$' or pkt[-3] != '#':
            raise ValueError('bad packet {}'.format(pkt))
        crc = (sum(ord(c) for c in pkt[1:-3]) % 256)
        crc2 = int(pkt[-2:], 16)
        if crc != crc2:
            raise ValueError('Checksum {} != {}'.format(crc, crc2))
        pkt = pkt[1:-3]
        return pkt

    def sendpkt(self, data, retries=10):
        """ sends data via the RSP protocol to the device """
        # Clean incoming queue:
        while not self.rxqueue.empty():
            self.rxqueue.get()
        self.logger.debug('GDB> %s', data)
        wire_data = self.rsp_pack(data)
        self.send(wire_data)
        res = self.recv()
        while res != '+':
            self.logger.warning('discards %s', res)
            self.logger.debug('resend-GDB> %s', data)
            self.send(wire_data)
            res = self.recv()
            retries -= 1
            if retries == 0:
                raise ValueError("retry fail")

    def recvpkt(self):
        """ Block until a packet is received """
        return self.recv()

    def recv(self):
        return self.rxqueue.get(timeout=2)

    def send(self, msg):
        """ Send ascii data to target """
        # self.logger.debug('--> %s', msg)
        self.transport.send(msg.encode('ascii'))

    def decodepkt(self, pkt, retries=10):
        """ blocks until it reads an RSP packet, and returns it's data"""
        while True:
            if pkt.startswith('$'):
                try:
                    res = self.rsp_unpack(pkt)
                except ValueError as ex:
                    self.logger.debug('GDB< %s', res)
                    self.logger.warning('Bad packet %s', ex)
                    self.send('-')
                else:
                    self.send('+')
                    self.logger.debug('GDB< %s', res)
                    return res
            else:
                self.logger.warning('discards %s', pkt)

            retries -= 1
            if retries == 0:
                raise ValueError('Retry fail!')

    def process_byte(self, byte):
        msg = self.packet_decoder.send(byte)
        if msg:
            # self.logger.debug('<-- %s', msg)
            if msg == '+':
                self.rxqueue.put(msg)
            else:
                pkt = self.decodepkt(msg)
                if pkt.startswith('S') or pkt.startswith('T'):
                    self.process_stop_status(pkt)
                else:
                    self.rxqueue.put(pkt)

    def sendbrk(self):
        """ sends break command to the device """
        self.logger.debug('Sending RAW stop 0x3')
        self.transport.send(bytes([0x03]))

    def get_pc(self):
        """ read the PC of the device """
        if self.pcstopval is not None:
            return self.pcstopval
        else:
            pc = self._get_register(self.arch.gdb_pc)
            self.logger.debug("PC value read:%x", pc)
            return pc

    def set_pc(self, value):
        """ set the PC of the device """
        self._set_register(self.arch.gdb_pc, value)
        self.logger.debug("PC value set:%x", value)

    def get_fp(self):
        """ read the frame pointer """
        return 0x100
        fp = self._get_register(self.arch.fp)
        self.logger.debug("FP value read:%x", fp)
        return fp

    def run(self):
        """ start the device """
        if self.status == DebugState.STOPPED:
            if self.swbrkpt is True and self.stopreason is BRKPOINT:
                pc = self.get_pc()
                self.set_pc(pc - 4)
            self.sendpkt("c")
            self.status = DebugState.RUNNING
            self.events.on_start()
        else:
            self.logger.warning('Cannot run, already running!')

    def restart(self):
        """ restart the device """
        if self.status == DebugState.STOPPED:
            self.set_pc(self.pcresval)
            self.run()
            self.status = DebugState.RUNNING
            self.events.on_start()

    def step(self):
        """ restart the device """
        if self.status == DebugState.STOPPED:
            if self.swbrkpt is True and self.stopreason is BRKPOINT:
                pc = self.get_pc()
                self.clear_breakpoint(pc - 4)
                self.set_pc(pc - 4)
            self.sendpkt("s")
            self.status = DebugState.RUNNING
            self.events.on_start()
        else:
            self.logger.warning('Cannot step, still running!')

    def nstep(self, count):
        """ restart the device """
        if self.status == DebugState.STOPPED:
            if self.swbrkpt is True and self.stopreason is BRKPOINT:
                pc = self.get_pc()
                self.clear_breakpoint(pc - 4)
                self.set_pc(pc - 4)
            self.sendpkt("n %x" % count)
            self.status = DebugState.RUNNING
            self.events.on_start()

    def stop(self):
        if self.status == DebugState.RUNNING:
            self.sendbrk()
            self.status = DebugState.STOPPED
            self.events.on_stop()
        else:
            self.logger.warning('Cannot stop if not running')

    def process_stop_status(self, pkt):
        """ Process stopped status like these:

        S05
        T0500:00112233;
        T05thread:01;
        """
        code = int(pkt[1:3], 16)  # signal number
        self.stopreason = code
        self.pcstopval = None

        if pkt.startswith('T'):
            rest = pkt[3:]
            for pair in map(str.strip, rest.split(';')):
                if not pair:
                    continue
                name, value = pair.split(':')
                if is_hex(name):
                    # We are dealing with a register value here!
                    reg_num = int(name, 16)
                    # self.arch.gdb_registers.index(self.arch.gdb_pc)
                    # TODO: fill a cache of registers
                    # data = bytes.fromhex(rest[3:-1])
                    # self.pcstopval, = struct.unpack('<I', data)

        if code & (BRKPOINT | INTERRUPT) != 0:
            self.logger.debug("Target stopped..")
            self.status = DebugState.STOPPED
            self.events.on_stop()
        else:
            self.logger.debug("Target running..")
            self.status = DebugState.RUNNING

    def get_status(self):
        return self.status

    def get_registers(self, registers):
        regs = self._get_general_registers()
        return regs

    def _get_general_registers(self):
        if self.status == DebugState.STOPPED:
            self.sendpkt("g")
            data = self.recvpkt()
            data = binascii.a2b_hex(data.encode('ascii'))
            res = {}
            offset = 0
            for register in self.arch.gdb_registers:
                size = register.bitsize // 8
                reg_data = data[offset:offset + size]
                res[register] = self._unpack_register(register, reg_data)
                offset += size
            if len(data) != offset:
                self.logger.error(
                    'Received %x bytes register data, processed %x' % (
                        len(data), offset))
            return res

    def set_registers(self, regvalues):
        if self.status == DebugState.STOPPED:
            data = bytearray()
            res = {}
            offset = 0
            for register in self.arch.gdb_registers:
                reg_data = self._pack_register(register, regvalues[register])
                size = register.bitsize // 8
                data[offset:offset + size] = reg_data
                offset += size
            data = binascii.b2a_hex(data).decode('ascii')
            self.sendpkt("G %s" % data)
            res = self.recvpkt()
            if res == 'OK':
                self.logger.debug('Register written')
            else:
                self.logger.warning('Registers writing failed: %s', res)

    def _get_register(self, register):
        """ Get a single register """
        if self.status == DebugState.STOPPED:
            idx = self.arch.gdb_registers.index(register)
            self.sendpkt("p %x" % idx)
            data = self.recvpkt()
            data = binascii.a2b_hex(data.encode('ascii'))
            return self._unpack_register(register, data)
        else:
            self.logger.warning(
                'Cannot read register %s while not stopped', register)
            return 0

    def _set_register(self, register, value):
        """ Set a single register """
        if self.status == DebugState.STOPPED:
            idx = self.arch.gdb_registers.index(register)
            value = self._pack_register(register, value)
            value = binascii.b2a_hex(value).decode('ascii')
            self.sendpkt("P %x=%s" % (idx, value))
            res = self.recvpkt()
            if res == 'OK':
                self.logger.debug('Register written')
            else:
                self.logger.warning('Register write failed: %s', res)

    def _unpack_register(self, register, data):
        """ Fetch a register from some data """
        fmts = {
            8: '<Q',
            4: '<I',
            2: '<H',
            1: '<B',
        }
        size = register.bitsize // 8
        if len(data) == size:
            if size == 3:
                value = data[0] + (data[1] << 8) + (data[2] << 16)
            else:
                value, = struct.unpack(fmts[size], data)
        else:
            self.logger.error('Could not read register %s', register)
            value = 0
        return value

    @staticmethod
    def _pack_register(register, value):
        """ Put some data in a register """
        fmts = {
            8: '<Q',
            4: '<I',
            2: '<H',
            1: '<B',
        }
        size = register.bitsize // 8
        data = struct.pack(fmts[size], value)
        return data

    def set_breakpoint(self, address: int):
        """ Set a breakpoint """
        if self.status == DebugState.STOPPED:
            self.sendpkt("Z0,%x,4" % address)
            res = self.recvpkt()
            if res == 'OK':
                self.logger.debug('Breakpoint set')
            else:
                self.logger.warning('Breakpoint not set: %s', res)
        else:
            self.logger.warning('Cannot set breakpoint, target not stopped!')

    def clear_breakpoint(self, address: int):
        """ Clear a breakpoint """
        if self.status == DebugState.STOPPED:
            self.sendpkt("z0,%x,4" % address)
            self.recvpkt()
        else:
            self.logger.warning('Cannot clear breakpoint, target not stopped!')

    def read_mem(self, address: int, size: int):
        """ Read memory from address """
        if self.status == DebugState.STOPPED:
            self.sendpkt("m %x,%x" % (address, size))
            ret = binascii.a2b_hex(self.recvpkt().encode('ascii'))
            return ret
        else:
            self.logger.warning('Cannot read memory, target not stopped!')

    def write_mem(self, address: int, data):
        """ Write memory """
        if self.status == DebugState.STOPPED:
            length = len(data)
            data = binascii.b2a_hex(data).decode('ascii')
            self.sendpkt("M %x,%x:%s" % (address, length, data))
            res = self.recvpkt()
            if res == 'OK':
                self.logger.debug('Memory written')
            else:
                self.logger.warning('Memory write failed: %s', res)
        else:
            self.logger.warning('Cannot write memory, target not stopped!')


def is_hex(text: str) -> bool:
    """ Check if the given text is hexadecimal """
    return all(c in string.hexdigits for c in text)
