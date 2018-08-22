""" Microblaze architecture.

Low level instruction class usage:

.. doctest::

    >>> from ppci.arch.microblaze import instructions, registers
    >>> i = instructions.Add(registers.R4, registers.R5, registers.R6)
    >>> str(i)
    'add R4, R5, R6'

"""


from .arch import MicroBlazeArch
from .registers import MicroBlazeRegister


__all__ = ('MicroBlazeArch', 'MicroBlazeRegister')
