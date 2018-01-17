"""
    Gdb debug client implementation for the debugger driver.
"""

import binascii
import logging
import struct
from threading import Thread, Lock
from queue import Queue
from .dbg import DebugDriver, STOPPED, RUNNING

INTERRUPT = 2
BRKPOINT = 5


class GdbDebugDriver(DebugDriver):
    """ Implement debugging via the GDB remote interface.

    GDB servers can communicate via the RSP protocol.

    Helpfull resources:

    http://www.embecosm.com/appnotes/ean4/
        embecosm-howto-rsp-server-ean4-issue-2.html

    """
    logger = logging.getLogger('gdbclient')

    def __init__(self, arch, transport, constat=STOPPED, pcresval=0,
                 swbrkpt=False):
        self.arch = arch
        self.transport = transport
        self.status = constat
        self.pcresval = pcresval
        self.pcstopval = None
        self.swbrkpt = swbrkpt
        self.stopreason = INTERRUPT
        self.rxqueue = Queue()
        self.rxthread = Thread(target=self.recv)
        self.rxthread.start()
        self.callbackstop = None
        self.callbackstart = None
        self.screenlock = Lock()
        if (constat == RUNNING):
            self.stop()

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
        self.logger.debug('GDB> %s', data)
        wire_data = self.rsp_pack(data).encode()
        self.transport.send(wire_data)
        res = self.rxqueue.get()
        while res != '+':
            self.logger.warning('discards %s', res)
            self.logger.debug('resend-GDB> %s', data)
            self.transport.send(wire_data)
            res = self.rxqueue.get()
            retries -= 1
            if retries == 0:
                raise ValueError("retry fail")

    def decodepkt(self, pkt, retries=10):
        """ blocks until it reads an RSP packet, and returns it's data"""
        while True:
            if pkt.startswith('$'):
                try:
                    res = self.rsp_unpack(pkt)
                except ValueError as ex:
                    self.logger.debug('GDB< %s', res)
                    self.logger.warning('Bad packet %s', ex)
                    self.transport.send(b'-')
                else:
                    self.transport.send(b'+')
                    self.logger.debug('GDB< %s', res)
                    return res
            else:
                self.logger.warning('discards %s', pkt)

            retries -= 1
            if retries == 0:
                raise ValueError('Retry fail!')

    def recv(self):
        """ Receive either a packet, or an ack """
        while True:
            readable = self.transport.rx_avail()
            if readable:
                data = self.transport.recv()
                if data == b'$':
                    res = bytearray()
                    res.extend(data)
                    while True:
                        res.extend(self.transport.recv())
                        if res[-1] == ord('#') and res[-2] != ord("'"):
                            res.extend(self.transport.recv())
                            res.extend(self.transport.recv())
                            pkt = self.decodepkt(res.decode('ascii'))
                            if pkt.startswith('S') or pkt.startswith('T'):
                                self.process_stop_status(pkt)
                            else:
                                self.rxqueue.put(pkt)
                            break
                elif data == b'+':
                    self.rxqueue.put(data.decode('ascii'))

    def sendbrk(self):
        """ sends break command to the device """
        self.logger.debug('Sending RAW stop 0x3')
        self.transport.send(bytes([0x03]))

    def get_pc(self):
        """ read the PC of the device """
        if (self.pcstopval is not None):
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
        if self.status == STOPPED:
            if (self.swbrkpt is True and self.stopreason is BRKPOINT):
                pc = self.get_pc()
                self.set_pc(pc - 4)
            self.sendpkt("c")
            self.status = RUNNING
            with self.screenlock:
                self.callbackstart()

    def restart(self):
        """ restart the device """
        if self.status == STOPPED:
            self.set_pc(self.pcresval)
            self.run()
            self.status = RUNNING
            with self.screenlock:
                self.callbackstart()

    def step(self):
        """ restart the device """
        if self.status == STOPPED:
            if (self.swbrkpt is True and self.stopreason is BRKPOINT):
                pc = self.get_pc()
                self.clear_breakpoint(pc - 4)
                self.set_pc(pc - 4)
            self.sendpkt("s")
            self.status = RUNNING
            with self.screenlock:
                self.callbackstart()

    def nstep(self, count):
        """ restart the device """
        if self.status == STOPPED:
            if (self.swbrkpt is True and self.stopreason is BRKPOINT):
                pc = self.get_pc()
                self.clear_breakpoint(pc - 4)
                self.set_pc(pc - 4)
            self.sendpkt("n %x" % count)
            self.status = RUNNING
            with self.screenlock:
                self.callbackstart()

    def stop(self):
        if self.status == RUNNING:
            self.sendbrk()

    def process_stop_status(self, pkt):
        code = int(pkt[1:3], 16)
        self.stopreason = code
        rest = pkt[3:]
        if (pkt.startswith('T') and int(rest[0:2], 16)
                == self.arch.gdb_registers.index(self.arch.gdb_pc)):
            data = bytes.fromhex(rest[3:-1])
            self.pcstopval, = struct.unpack('<I', data)
        else:
            self.pcstopval = None
        if (code & (BRKPOINT | INTERRUPT) != 0):
            self.logger.debug("Target stopped..")
            self.status = STOPPED
            if self.callbackstop:
                with self.screenlock:
                    self.callbackstop()
        else:
            self.logger.debug("Target running..")
            self.status = RUNNING

    def get_status(self):
        return self.status

    def get_registers(self, registers):
        regs = self._get_general_registers()
        return regs

    def _get_general_registers(self):
        if self.status == STOPPED:
            self.sendpkt("g")
            data = self.rxqueue.get()
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
        if self.status == STOPPED:
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
            res = self.rxqueue.get()
            if res == 'OK':
                self.logger.debug('Register written')
            else:
                self.logger.warning('Registers writing failed: %s', res)

    def _get_register(self, register):
        """ Get a single register """
        if self.status == STOPPED:
            idx = self.arch.gdb_registers.index(register)
            self.sendpkt("p %x" % idx)
            data = self.rxqueue.get()
            data = binascii.a2b_hex(data.encode('ascii'))
            return self._unpack_register(register, data)

    def _set_register(self, register, value):
        """ Set a single register """
        if self.status == STOPPED:
            idx = self.arch.gdb_registers.index(register)
            value = self._pack_register(register, value)
            value = binascii.b2a_hex(value).decode('ascii')
            self.sendpkt("P %x=%s" % (idx, value))
            res = self.rxqueue.get()
            if res == 'OK':
                self.logger.debug('Register written')
            else:
                self.logger.warning('Register write failed: %s', res)

    @staticmethod
    def _unpack_register(register, data):
        """ Fetch a register from some data """
        fmts = {
            8: '<Q',
            4: '<I',
            2: '<H',
            1: '<B',
        }
        size = register.bitsize // 8
        assert len(data) == size
        if size == 3:
            value = data[0] + (data[1] << 8) + (data[2] << 16)
        else:
            value, = struct.unpack(fmts[size], data)
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

    def set_breakpoint(self, address):
        """ Set a breakpoint """
        if self.status == STOPPED:
            self.sendpkt("Z0,%x,4" % address)
            res = self.rxqueue.get()
            if res == 'OK':
                self.logger.debug('Breakpoint set')
            else:
                self.logger.warning('Breakpoint not set: %s', res)

    def clear_breakpoint(self, address):
        """ Clear a breakpoint """
        if self.status == STOPPED:
            self.sendpkt("z0,%x,4" % address)
            self.rxqueue.get()

    def read_mem(self, address, size):
        """ Read memory from address """
        if self.status == STOPPED:
            self.sendpkt("m %x,%x" % (address, size))
            ret = binascii.a2b_hex(self.rxqueue.get().encode('ascii'))
            return ret

    def write_mem(self, address, data):
        """ Write memory """
        if self.status == STOPPED:
            length = len(data)
            data = binascii.b2a_hex(data).decode('ascii')
            self.sendpkt("M %x,%x:%s" % (address, length, data))
            res = self.rxqueue.get()
            if res == 'OK':
                self.logger.debug('Memory written')
            else:
                self.logger.warning('Memory write failed: %s', res)
