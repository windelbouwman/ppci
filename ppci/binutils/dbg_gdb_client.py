"""
    Gdb debug client implementation for the debugger driver.
"""

import binascii
import logging
import socket
import select
import struct
import time 
from .dbg import DebugDriver, STOPPED, RUNNING


class GdbDebugDriver(DebugDriver):
    """ Implement debugging via the GDB remote interface.

    GDB servers can communicate via the RSP protocol.

    Helpfull resources:

    http://www.embecosm.com/appnotes/ean4/
        embecosm-howto-rsp-server-ean4-issue-2.html

    """
    logger = logging.getLogger('gdbclient')

    def __init__(self, arch, port=1234, constat=STOPPED):
        self.arch = arch
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", port))
        time.sleep(1)
        self.status = constat
        if(constat == RUNNING):
            self.stop()


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
        readable, _, _ = select.select([self.sock], [], [], 0)
        if readable:
            self.process_stop_status()
        self.logger.debug('GDB> %s', data)
        wire_data = self.rsp_pack(data).encode()
        self.sock.send(wire_data)
        res = self.recv()
        while res != '+':
            self.logger.warning('discards %s', res)
            self.logger.debug('resend-GDB> %s', data)
            self.sock.send(wire_data)
            res = self.recv()
            retries -= 1
            if retries == 0:
                raise ValueError("retry fail")

    def readpkt(self, retries=10):
        """ blocks until it reads an RSP packet, and returns it's data"""
        while True:
            pkt = self.recv()
            if pkt.startswith('$'):
                try:
                    res = self.rsp_unpack(pkt)
                except ValueError as ex:
                    self.logger.debug('GDB< %s', res)
                    self.logger.warning('Bad packet %s', ex)
                    self.sock.send(b'-')
                else:
                    self.sock.send(b'+')
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
            data = self.sock.recv(1)
            if data == b'+':
                return data.decode('ascii')
            elif data == b'$':
                res = bytearray()
                res.extend(data)
                while True:
                    res.extend(self.sock.recv(1))
                    if res[-1] == ord('#') and res[-2] != ord("'"):
                        res.extend(self.sock.recv(1))
                        res.extend(self.sock.recv(1))
                        return res.decode('ascii')
            else:
                print('UNKNOWN:', data)

    def process_byte(self, b):
        pass

    def _process_incoming(self):
        """ Process all incoming bytes """
        while True:
            readable, _, _ = select.select([self.sock], [], [], 0)
            if readable:
                b = self.sock.recv(1)
                self.process_byte(b)
            else:
                break

    def sendbrk(self):
        """ sends break command to the device """
        self.logger.debug('Sending RAW stop 0x3')
        self.sock.send(bytes([0x03]))

    def get_pc(self):
        """ read the PC of the device """
        pc = self._get_register(self.arch.gdb_pc)
        self.logger.debug("PC value read:%x", pc)
        return pc

    def get_fp(self):
        """ read the frame pointer """
        return 0x100
        fp = self._get_register(self.arch.fp)
        self.logger.debug("FP value read:%x", fp)
        return fp

    def run(self):
        """ start the device """
        if self.status == STOPPED:
            self.sendpkt("c")
            # res = self.readpkt()
            # print(res)
            self.status = RUNNING

    def restart(self):
        """ restart the device """
        if self.status == STOPPED:
            self.sendpkt("c00000080")
            res = self.readpkt()
            print(res)
        self.status = RUNNING

    def step(self):
        """ restart the device """
        if self.status == STOPPED:
            self.sendpkt("s")
            self.process_stop_status()

    def nstep(self, count):
        """ restart the device """
        if self.status == STOPPED:
            self.sendpkt("n %x" %count)
            self.process_stop_status()


    def stop(self):
        self.sendbrk()
        self.status = STOPPED
        self.process_stop_status()

    def process_stop_status(self):
        res = self.readpkt()
        if res.startswith('S'):
            code = int(res[1:3], 16)
        elif res.startswith('T'):
            code = int(res[1:3], 16)
            rest = res[3:]
            print('TODO', rest.split(';'))
        else:
            raise NotImplementedError(res)

        if code == 5:
            self.logger.debug("Target stopped..")
            self.status = STOPPED
        else:
            self.logger.debug("Target running..")
            self.status = RUNNING

    def get_status(self):
        return self.status

    def get_registers(self, registers):
        regs = self._get_general_registers()
        return regs

    def _get_general_registers(self):
        self.sendpkt("g")
        data = self.readpkt()
        data = binascii.a2b_hex(data.encode('ascii'))
        res = {}
        offset = 0
        for register in self.arch.gdb_registers:
            size = register.bitsize // 8
            reg_data = data[offset:offset+size]
            res[register] = self._unpack_register(register, reg_data)
            offset += size
        assert len(data) == offset, '%x %x' % (len(data), offset)
        return res

    def _get_register(self, register):
        """ Get a single register """
        idx = self.arch.gdb_registers.index(register)
        self.sendpkt("p %x" % idx)
        data = self.readpkt()
        data = binascii.a2b_hex(data.encode('ascii'))
        return self._unpack_register(register, data)

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

    def set_breakpoint(self, address):
        """ Set a breakpoint """
        self.sendpkt("Z0,%x,4" % address)
        res = self.readpkt()
        if res == 'OK':
            self.logger.debug('Breakpoint set')
        else:
            self.logger.warning('Breakpoint not set: %s', res)

    def clear_breakpoint(self, address):
        """ Clear a breakpoint """
        self.sendpkt("z0,%x,4" % address)
        self.readpkt()

    def read_mem(self, address, size):
        """ Read memory from address """
        self.sendpkt("m %x,%x" % (address, size))
        ret = binascii.a2b_hex(self.readpkt().encode('ascii'))
        return ret

    def write_mem(self, address, data):
        """ Write memory """
        length = len(data)
        data = binascii.b2a_hex(data).decode('ascii')
        self.sendpkt("M %x,%x:%s" % (address, length, data))
