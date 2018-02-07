from .debug_driver import DebugDriver, DebugState


class DummyDebugDriver(DebugDriver):
    """ Stub implementation of the debug driver """
    def __init__(self):
        super().__init__()
        self.status = DebugState.STOPPED

    def run(self):
        self.status = DebugState.RUNNING

    def restart(self):
        self.status = DebugState.RUNNING

    def step(self):
        pass

    def stop(self):
        self.status = DebugState.STOPPED

    def get_status(self):
        return self.status

    def get_registers(self, registers):
        return {r: 0 for r in registers}

    def get_pc(self):
        return 0

    def get_fp(self):
        return 0

    def set_breakpoint(self, address):
        pass

    def clear_breakpoint(self, address):
        pass

    def read_mem(self, address, size):
        return bytes(size)

    def write_mem(self, address, data):
        pass

    def update_status(self):
        pass
