"""

.. autoclass:: ppci.arch.arch.Architecture
    :members:


.. autoclass:: ppci.arch.arch.Frame
    :members:

.. autoclass:: ppci.arch.isa.Isa
    :members:


.. autoclass:: ppci.arch.registers.Register
    :members: is_colored


.. autoclass:: ppci.arch.encoding.Instruction
    :members:

"""

from .arch import Architecture, Frame
from .isa import Isa


__all__ = ['Architecture', 'Frame', 'Isa']
