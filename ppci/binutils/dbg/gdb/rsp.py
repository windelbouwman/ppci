""" Implement the RSP protocol which is used in gdb.

A packet is send, and then it is acknowledged by a '+'.

"""

import logging
from queue import Queue
from threading import Lock


class RspHandler:
    """ Handle packet handling with the '+' as ack and '-' as nack """
    logger = logging.getLogger('rsp-handler')
    verbose = False

    def __init__(self, transport):
        self.transport = transport
        self.transport.on_byte = self._process_byte

        self._packet_decoder = decoder()
        next(self._packet_decoder)  # Bump decoder to first byte.

        # ACHTUNG: multithreaded code ahead:
        self._ack_queue = Queue(maxsize=1)
        self._lock = Lock()
        self.on_message = None

    def sendpkt(self, data, retries=10):
        """ sends data via the RSP protocol to the device """
        with self._lock:
            wire_data = self.rsp_pack(data)
            self.logger.debug('--> %s', wire_data)
            self.send(wire_data)
            res = self._ack_queue.get(timeout=0.5)
            while res != '+':
                self.logger.warning('discards %s', res)
                self.logger.debug('resend-GDB> %s', data)
                self.send(wire_data)
                res = self._ack_queue.get(timeout=0.5)
                retries -= 1
                if retries == 0:
                    raise ValueError("retry fail")

    def send(self, msg):
        """ Send ascii data to target """
        if self.verbose:
            self.logger.debug('--> %s', msg)
        self.transport.send(msg.encode('ascii'))

    def _process_byte(self, byte):
        msg = self._packet_decoder.send(byte)
        if msg:
            if self.verbose:
                self.logger.debug('<-- %s', msg)

            if msg in ['+', '-']:
                self._ack_queue.put(msg, timeout=0.5)
            else:
                self.decodepkt(msg)

    def decodepkt(self, pkt):
        """ blocks until it reads an RSP packet, and returns it's data"""
        self.logger.debug('<-- %s', pkt)
        if pkt.startswith('$'):
            try:
                res = self.rsp_unpack(pkt)
            except ValueError as ex:
                self.logger.warning('Bad packet %s', ex)
                self.send('-')
            else:
                self.send('+')
                self.on_message(res)
        else:
            self.logger.warning('discards %s', pkt)

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
