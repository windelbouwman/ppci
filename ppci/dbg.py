"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import logging
import xmlrpc.client
import xmlrpc.server
from .api import fix_target


# States:
STOPPED = 0
RUNNING = 1
FINISHED = 2


class SubscribleEvent:
    def __init__(self):
        self.callbacks = []

    def fire(self, *args):
        for callback in self.callbacks:
            callback(*args)

    def subscribe(self, callback):
        self.callbacks.append(callback)


class Debugger:
    """
        Main interface to the debugger.
        Give it a target architecture for which it must debug
        #TODO: and perhaps give it a plugin to connect to hardware?
    """
    def __init__(self, arch, target_connector):
        self.arch = fix_target(arch)
        self.server = target_connector
        self.logger = logging.getLogger('dbg')
        self.connection_event = SubscribleEvent()
        self.state_event = SubscribleEvent()
        self.register_names = self.get_register_names()
        self.register_values = {rn: 0 for rn in self.register_names}

        # Subscribe to events:
        self.state_event.subscribe(self.on_halted)

    def on_halted(self):
        new_values = self.get_register_values(self.register_names)
        self.register_values.update(new_values)

    # Connection:
    def connect(self, uri):
        self.logger.info('Connecting to %s', uri)
        self.server = xmlrpc.client.ServerProxy(uri)
        if self.is_connected:
            self.connection_event.fire()
        else:
            self.server = None

    def disconnect(self):
        self.logger.info('Disconnecting')
        self.server = None
        self.connection_event.fire()

    @property
    def is_connected(self):
        if not self.server:
            return False
        return self.server.ping()

    # Start stop parts:
    def run(self):
        self.logger.info('Run')
        self.server.run()
        self.state_event.fire()

    def stop(self):
        self.logger.info('Stop')
        self.server.stop()
        self.state_event.fire()

    def step(self):
        self.server.step()
        self.state_event.fire()

    def get_status(self):
        return self.server.get_status()

    status = property(get_status)

    @property
    def is_running(self):
        return self.status == RUNNING

    @property
    def is_halted(self):
        return not self.is_running

    # Registers:
    def get_register_names(self):
        return [reg.name for reg in self.arch.registers]

    def get_register_values(self, registers):
        """ Get a dictionary of register values """
        return self.server.get_registers(registers)

    def set_register(self, register, value):
        self.logger.info('Setting register {} to {}'.format(register, value))
        # TODO!


class DebugServer:
    """ Inherit this class to expose a target interface """
    def ping(self):
        return True

    def serve(self):
        """ Start to serve the debugger interface """
        server = xmlrpc.server.SimpleXMLRPCServer(
            ('localhost', 8079), allow_none=True)
        server.register_instance(self)
        server.register_introspection_functions()
        server.serve_forever()


class DummyDebugServer(DebugServer):
    def __init__(self):
        self.status = STOPPED

    def run(self):
        self.status = RUNNING

    def step(self):
        pass

    def stop(self):
        self.status = STOPPED

    def get_status(self):
        return self.status
