"""
    Gdb debug client implementation for the debugger driver.
"""

import abc
import binascii
import logging
import struct
import string
import queue
from threading import Thread
from ..debug_driver import DebugDriver, DebugState
from .rsp import RspHandler

INTERRUPT = 2
BRKPOINT = 5


class GdbCommHandler(metaclass=abc.ABCMeta):
    """ This class deals with the logic of communication """
    def shake(self, message):
        pass


class ThreadedCommHandler(GdbCommHandler):
    """ A comm handler that uses a thread """
    def __init__(self):
        self.rxqueue = queue.Queue()

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
        self._register_value_cache = {}  # Cached map of register values
        self.swbrkpt = swbrkpt
        self.stopreason = INTERRUPT

        self._message_handler = None
        self._stop_msg_queue = queue.Queue()
        self._msg_queue = queue.Queue(maxsize=1)
        self._rsp = RspHandler(transport)
        self._rsp.on_message = self._handle_message

    def __str__(self):
        return 'Gdb debug driver via {}'.format(self.transport)

    def connect(self):
        """ Connect to the target """
        self._message_handler = Thread(target=self._handle_stop_queue)
        self._message_handler.start()
        self.transport.connect()
        # self.send('?')

    def disconnect(self):
        """ Disconnect the client """
        self.transport.disconnect()
        self._stop_msg_queue.put(1337)
        self._message_handler.join()

    def _handle_stop_queue(self):
        self.logger.debug('stop thread started')
        msg = self._stop_msg_queue.get()
        while msg != 1337:
            self._process_stop_status(msg)
            msg = self._stop_msg_queue.get()
        self.logger.debug('stop thread finished')

    def run(self):
        """ start the device """
        if self.status == DebugState.STOPPED:
            self._prepare_continue()
        else:
            self.logger.warning('Already running!')

        self._send_message("c")
        self._start()

    def restart(self):
        """ restart the device """
        if self.status == DebugState.STOPPED:
            self.set_pc(self.pcresval)
            self.run()
        else:
            self.logger.warning('Cannot restart, still running!')

    def step(self):
        """ Single step the device """
        if self.status == DebugState.STOPPED:
            self._prepare_continue()
            self._send_message("s")
            self._start()
        else:
            self.logger.warning('Cannot step, still running!')

    def nstep(self, count):
        """ Single step `count` times """
        if self.status == DebugState.STOPPED:
            self._prepare_continue()
            self._send_message("n %x" % count)
            self._start()
        else:
            self.logger.warning('Cannot step, still running!')

    def _prepare_continue(self):
        """ Set program counter somewhat back to continue """
        if self.swbrkpt and self.stopreason is BRKPOINT:
            pc = self.get_pc()
            self.clear_breakpoint(pc - 4)
            self.set_pc(pc - 4)

    def stop(self):
        if self.status == DebugState.RUNNING:
            self._sendbrk()
        else:
            self.logger.warning('Cannot stop if not running')

    def _sendbrk(self):
        """ sends break command to the device """
        self.logger.debug('Sending RAW stop 0x3')
        self.transport.send(bytes([0x03]))

    def _start(self):
        """ Update state to started """
        self.status = DebugState.RUNNING
        self._register_value_cache.clear()
        self.events.on_start()

    def _stop(self):
        self.status = DebugState.STOPPED
        self.events.on_stop()

    def _process_stop_status(self, pkt):
        """ Process stopped status like these:

        S05
        T0500:00112233;
        T05thread:01;
        """
        assert pkt.startswith(('S', 'T'))
        code = int(pkt[1:3], 16)  # signal number
        self.stopreason = code

        if pkt.startswith('T'):
            rest = pkt[3:]
            for pair in map(str.strip, rest.split(';')):
                if not pair:
                    continue
                name, value = pair.split(':')
                if is_hex(name):
                    # We are dealing with a register value here!
                    reg_num = int(name, 16)
                    #self.logger.error('%s', reg_num)
                    if reg_num == self.arch.gdb_registers.index(self.arch.gdb_pc):
                        # TODO: fill a cache of registers
                        data = bytes.fromhex(rest[3:-1])
                        self.pcstopval, = struct.unpack('<I', data)

        if code & (BRKPOINT | INTERRUPT) != 0:
            self.logger.debug("Target stopped..")

            # If the program counter was not given in the stop packet
            # retrieve it now
            if self.arch.gdb_pc not in self._register_value_cache:
                self.logger.debug('Retrieving general registers')
                self._get_general_registers()

            self._stop()
        else:
            self.logger.debug("Target running..")
            self.status = DebugState.RUNNING

    def get_status(self):
        return self.status

    def get_pc(self):
        """ read the PC of the device """
        if self.status == DebugState.STOPPED:
            return self._get_register(self.arch.gdb_pc)
        else:
            return 0

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

    def get_registers(self, registers):
        if self.status == DebugState.STOPPED:
            regs = self._get_general_registers()
        else:
            self.logger.warning('Cannot read registers while running')
            regs = {}
        return regs

    def _get_general_registers(self):
        """ Execute the gdb `g` command """
        data = self._send_command("g")
        data = binascii.a2b_hex(data.encode('ascii'))
        res = {}
        offset = 0
        for register in self.arch.gdb_registers:
            size = register.bitsize // 8
            reg_data = data[offset:offset + size]
            value = self._unpack_register(register, reg_data)
            res[register] = value
            # self.logger.debug('reg %s = %s', register, value)
            self._register_value_cache[register] = value
            offset += size

        if len(data) != offset:
            self.logger.error(
                'Received %s bytes register data, processed %s',
                len(data), offset)
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
            res = self._send_command("G %s" % data)
            if res == 'OK':
                self.logger.debug('Register written')
            else:
                self.logger.warning('Registers writing failed: %s', res)

    def _get_register(self, register):
        """ Get a single register """
        if self.status == DebugState.STOPPED:
            if register in self._register_value_cache:
                value = self._register_value_cache[register]
            else:
                idx = self.arch.gdb_registers.index(register)
                data = self._send_command("p %x" % idx)
                data = binascii.a2b_hex(data.encode('ascii'))
                value = self._unpack_register(register, data)
                self._register_value_cache[register] = value
            return value
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
            res = self._send_command("P %x=%s" % (idx, value))
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
            res = self._send_command("Z0,%x,4" % address)
            if res == 'OK':
                self.logger.debug('Breakpoint set')
            else:
                self.logger.warning('Breakpoint not set: %s', res)
        else:
            self.logger.warning('Cannot set breakpoint, target not stopped!')

    def clear_breakpoint(self, address: int):
        """ Clear a breakpoint """
        if self.status == DebugState.STOPPED:
            res = self._send_command("z0,%x,4" % address)
            if res == 'OK':
                self.logger.debug('Breakpoint cleared')
            else:
                self.logger.warning('Breakpoint not cleared: %s', res)
        else:
            self.logger.warning('Cannot clear breakpoint, target not stopped!')

    def read_mem(self, address: int, size: int):
        """ Read memory from address """
        if self.status == DebugState.STOPPED:
            res = self._send_command("m %x,%x" % (address, size))
            ret = binascii.a2b_hex(res.encode('ascii'))
            return ret
        else:
            self.logger.warning('Cannot read memory, target not stopped!')
            return bytes()

    def write_mem(self, address: int, data):
        """ Write memory """
        if self.status == DebugState.STOPPED:
            length = len(data)
            data = binascii.b2a_hex(data).decode('ascii')
            res = self._send_command("M %x,%x:%s" % (address, length, data))
            if res == 'OK':
                self.logger.debug('Memory written')
            else:
                self.logger.warning('Memory write failed: %s', res)
        else:
            self.logger.warning('Cannot write memory, target not stopped!')

    def _handle_message(self, message):
        # Filter stop packets:
        if message.startswith(('T', 'S')):
            self._stop_msg_queue.put(message)
        else:
            self._msg_queue.put(message)

    def _send_command(self, command):
        """ Send a gdb command a receive a response """
        self._send_message(command)
        return self._recv_message()

    def _recv_message(self, timeout=3):
        """ Block until a packet is received """
        return self._msg_queue.get(timeout=timeout)

    def _send_message(self, message):
        self._rsp.sendpkt(message)


def is_hex(text: str) -> bool:
    """ Check if the given text is hexadecimal """
    return all(c in string.hexdigits for c in text)
