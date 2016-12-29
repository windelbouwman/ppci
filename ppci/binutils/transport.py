"""
    Communication channel for debug client.
"""

import socket
import select


class Transport:
    """
        Inherit this for each debug communication channel
    """

    def rx_avail(self):
        raise NotImplementedError()

    def recv(self):
        raise NotImplementedError()

    def send(self):
        raise NotImplementedError()


class TCP(Transport):
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", port))

    def rx_avail(self):
        readable, _, _ = select.select([self.sock], [], [], 0)
        return(readable)

    def recv(self):
        return(self.sock.recv(1))

    def send(self, data):
        self.sock.send(data)
