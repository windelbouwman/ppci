"""
    Debugger. The debugger always operates in remote mode like gdb.

    Start the debug server for your target and connect to it using the
    debugger interface.
"""

import logging
from ..api import fix_target, fix_object
from .disasm import Disassembler
from .outstream import RecordingOutputStream


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
        self.disassembler = Disassembler(arch)
        self.driver = target_connector
        self.logger = logging.getLogger('dbg')
        self.connection_event = SubscribleEvent()
        self.state_event = SubscribleEvent()
        self.register_names = self.get_register_names()
        self.register_values = {rn: 0 for rn in self.register_names}
        self.obj = None

        # Subscribe to events:
        self.state_event.subscribe(self.on_halted)

        # Fire initial change:
        self.state_event.fire()

    def on_halted(self):
        if self.is_halted:
            new_values = self.get_register_values(self.register_names)
            self.register_values.update(new_values)

    # Start stop parts:
    def run(self):
        self.logger.info('run')
        self.driver.run()
        self.state_event.fire()

    def stop(self):
        self.logger.info('stop')
        self.driver.stop()
        self.state_event.fire()

    def set_breakpoint(self, filename, row):
        self.logger.info('set breakpoint %s:%i', filename, row)
        address = self.find_address(filename, row)
        if address is None:
            self.logger.warn('Could find address for breakpoint')
        self.driver.set_breakpoint(address)

    def clear_breakpoint(self, filename, row):
        self.logger.info('clear breakpoint %s:%i', filename, row)

    def step(self):
        self.logger.info('step')
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

    # debug info:
    def load_symbols(self, obj):
        """ Load debug symbols from object file """
        obj = fix_object(obj)
        # verify the contents of the object with the memory image
        assert self.is_halted
        for image in obj.images:
            vdata = image.data
            adata = self.read_mem(image.location, len(vdata))
            assert vdata == adata
        self.logger.info('memory image validated!')
        self.obj = obj

    def find_pc(self):
        """ Given the current program counter (pc) determine the source """
        if not self.obj:
            return
        pc = self.get_pc()
        for debug in self.obj.debug:
            #print(debug)
            addr = self.obj.get_section(debug.section).address + debug.offset
            if pc == addr:
                print('MATCH', debug)
                loc = debug.data.loc
                return loc.filename, loc.row

    def find_address(self, filename, row):
        """ Given a filename and a row, determine the address """
        pass
        for debug in self.obj.debug:
            if not hasattr(debug.data, 'loc'):
                continue
            loc = debug.data.loc
            if loc.filename == filename and loc.row == row:
                addr = self.obj.get_section(debug.section).address + debug.offset
                return addr
        self.logger.warn('Could find address for %s:%i', filename, row)

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

    def write_mem(self, address, data):
        return self.driver.write_mem(address, data)

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

    def get_mixed(self):
        """ Get source lines and assembly lines """
        pass


class DebugDriver:
    """ Inherit this class to expose a target interface """
    def run(self):
        raise NotImplementedError()

    def step(self):
        raise NotImplementedError()

    def set_breakpoint(self, address):
        raise NotImplementedError()


class DummyDebugDriver(DebugDriver):
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

    def get_registers(self, registers):
        return {r: 0 for r in registers}

    def set_breakpoint(self, address):
        pass


class DebugCli:
    """
        Implement a simple console-based debugger interface.
    """
    def __init__(self, debugger):
        self.debugger = debugger

    def run(self):
        """ Enter the command loop """
        while True:
            cmd = input('(ppci-dbg)> ')
            # TODO: implement more commands
            if cmd == 'q' or cmd == 'quit':
                break
            elif cmd == 's' or cmd == 'step':
                self.debugger.step()
            elif cmd == 'c' or cmd == 'continue':
                self.debugger.run()
            elif cmd == '?' or cmd == 'h' or cmd == 'help':
                print('c: continue the program')
                print('q: quit the debugger')
                print('s: perform a single step')
                print('help: display this help')
            else:
                print('Unknown command (enter help for a command list)')
