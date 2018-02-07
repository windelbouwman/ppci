""" Debug driver interface. """
import abc
import enum
from .event import Events


class DebugState(enum.Enum):
    """ Debug states """
    STOPPED = 0
    RUNNING = 1
    FINISHED = 2
    UNKNOWN = 99


class DebugDriver(metaclass=abc.ABCMeta):  # pragma: no cover
    """ Degug driver interface.

    Inherit this class to expose a target interface. This class implements
    primitives for a given hardware target.
    """

    def __init__(self):
        self.events = Events()

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
