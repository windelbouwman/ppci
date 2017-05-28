"""
    Communication channel for debug client.
"""

import abc
import socket
import select


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
        raise NotImplementedError()


class TCP(Transport):
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", port))
        self._port = port

    def __str__(self):
        return 'Tcp localhost:{}'.format(self._port)

    def rx_avail(self):
        readable, _, _ = select.select([self.sock], [], [], 0)
        return(readable)

    def recv(self):
        return(self.sock.recv(1))

    def send(self, data):
        self.sock.send(data)
