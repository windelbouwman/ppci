"""
    Communication channel for debug client.
"""

import abc
import logging
import socket
import select
from threading import Thread


class Transport(metaclass=abc.ABCMeta):
    """
        Inherit this for each debug communication channel
    """

    @abc.abstractmethod
    def rx_avail(self):  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def recv(self):  # pragma: no cover
        raise NotImplementedError()

    @abc.abstractmethod
    def send(self):  # pragma: no cover
        """ Send data """
        raise NotImplementedError()


class ThreadedTransport(Transport):
    logger = logging.getLogger('transport')


class TCP(ThreadedTransport):
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._port = port
        self.on_byte = None
        self._rxthread = None

    def connect(self):
        """ Connect to socket and start thread """
        host = 'localhost'
        self.logger.info('Connecting to %s:%s', host, self._port)
        self.sock.connect((host, self._port))
        self._running = True
        self._rxthread = Thread(target=self.recv_thread)
        self._rxthread.start()

    def disconnect(self):
        """ Stop thread gracefully """
        self.logger.info('Disconnecting')
        self._running = False
        self._rxthread.join()
        self._rxthread = None
        self.sock.close()
        self.logger.info('Disconnected')

    def __str__(self):
        return 'Tcp localhost:{}'.format(self._port)

    def rx_avail(self):
        readable, _, _ = select.select([self.sock], [], [], 0)
        return readable

    def recv(self):
        """ Receive a single byte """
        return self.sock.recv(1)

    def send(self, data):
        """ Send data """
        self.sock.send(data)

    def recv_thread(self):
        """ Receive either a packet, or an ack """
        self.logger.info('Receiver thread started')
        try:
            while self._running:
                readable = self.rx_avail()
                if readable:
                    data = self.recv()
                    if data:
                        if self.on_byte:
                            self.on_byte(data)
                    else:  # No data means socket closed.
                        break
        #except Exception as ex:
        #    self.logger.error('Receiver thread terminated: %s', ex)
        finally:
            self.logger.info('Receiver thread finished')
