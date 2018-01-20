""" Debug driver interface. """
import abc
import enum


class DebugState(enum.Enum):
    """ Debug states """
    STOPPED = 0
    RUNNING = 1
    FINISHED = 2


class DebugDriver(metaclass=abc.ABCMeta):  # pragma: no cover
    """ Degug driver interface.

    Inherit this class to expose a target interface. This class implements
    primitives for a given hardware target.
    """

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def step(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    def get_status(self):
        raise NotImplementedError()

    def get_pc(self):
        raise NotImplementedError()

    def get_fp(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def set_breakpoint(self, address):
        raise NotImplementedError()

    def get_registers(self, registers):
        """ Get the values for a range of registers """
        raise NotImplementedError()


class DummyDebugDriver(DebugDriver):
    def __init__(self):
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
