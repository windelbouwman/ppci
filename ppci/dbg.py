"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import logging
from .api import fix_target
from .disasm import Disassembler
from .binutils.outstream import RecordingOutputStream


# States:
STOPPED = 0
RUNNING = 1
FINISHED = 2


class DbgInfo:
    pass


class LineInfo:
    pass


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
        self.disassembler = Disassembler(arch)
        self.driver = target_connector
        self.logger = logging.getLogger('dbg')
        self.connection_event = SubscribleEvent()
        self.state_event = SubscribleEvent()
        self.register_names = self.get_register_names()
        self.register_values = {rn: 0 for rn in self.register_names}

        # Subscribe to events:
        self.state_event.subscribe(self.on_halted)

        # Fire initial change:
        self.state_event.fire()

    def on_halted(self):
        if self.is_halted:
            new_values = self.get_register_values(self.register_names)
            self.register_values.update(new_values)

    # Connection:
    def connect(self, uri):
        self.logger.info('Connecting to %s', uri)
        # self.driver = xmlrpc.client.ServerProxy(uri)
        if self.is_connected:
            self.connection_event.fire()
        else:
            self.driver = None

    def disconnect(self):
        self.logger.info('Disconnecting')
        self.driver = None
        self.connection_event.fire()

    @property
    def is_connected(self):
        if not self.driver:
            return False
        return self.driver.ping()

    # Start stop parts:
    def run(self):
        self.logger.info('Run')
        self.driver.run()
        self.state_event.fire()

    def stop(self):
        self.logger.info('Stop')
        self.driver.stop()
        self.state_event.fire()

    def step(self):
        self.driver.step()
        self.state_event.fire()

    def get_status(self):
        return self.driver.get_status()

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
        return self.driver.get_registers(registers)

    def set_register(self, register, value):
        self.logger.info('Setting register {} to {}'.format(register, value))
        # TODO!

    # Memory:
    def read_mem(self, address, size):
        return self.driver.read_mem(address, size)

    # Disassembly:
    def get_pc(self):
        """ Get the program counter """
        return self.driver.get_pc()

    def get_disasm(self):
        """ Get instructions around program counter """
        loc = self.get_pc()
        address = loc - 20
        data = self.read_mem(address, 40)
        instructions = []
        outs = RecordingOutputStream(instructions)
        self.disassembler.disasm(data, outs, address=address)
        return instructions


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
