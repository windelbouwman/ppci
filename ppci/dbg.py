"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import xmlrpc.client
import xmlrpc.server


class Debugger:
    """ Main interface to the debugger """
    def __init__(self):
        self.server = None

    def connect(self, uri):
        self.server = xmlrpc.client.ServerProxy(uri)

    def disconnect(self):
        self.server = None

    @property
    def is_connected(self):
        if not self.server:
            return False
        return self.server.ping()

    def run(self):
        self.server.run()

    def stop(self):
        self.server.stop()

    def get_status(self):
        return self.server.get_status()

    def get_registers(self):
        return []


class DebugServer:
    """ Inherit this class to expose a target interface """
    def ping(self):
        return True

    def serve(self):
        """ Start to serve the debugger interface """
        server = xmlrpc.server.SimpleXMLRPCServer(('localhost', 8079))
        server.register_instance(self)
        server.register_introspection_functions()
        server.serve_forever()


class DummyDebugServer(DebugServer):
    def __init__(self):
        self.status = 0

    def run(self):
        self.status = 1

    def stop(self):
        self.status = 0

    def get_status(self):
        return self.status


class LinuxDebugger(DebugServer):
    """ Implements a debugger backend """
    pass
