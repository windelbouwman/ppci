"""

.. autoclass:: ppci.arch.arch.Architecture
    :members:

.. autoclass:: ppci.arch.arch_info.ArchInfo
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

import sys
import platform

from .arch import Architecture, Frame
from .isa import Isa


def get_current_arch():
    """ Try to get the architecture for the current platform """
    if sys.platform.startswith('win'):
        machine = platform.machine()
        if machine == 'AMD64':
            return get_arch('x86_64:wincc')
    elif sys.platform == 'linux':
        if platform.architecture()[0] == '64bit':
            return get_arch('x86_64')


def get_arch(arch):
    """ Try to return an architecture instance.

    Args:
        arch: can be a string in the form of arch:option1:option2

    .. doctest::

        >>> from ppci.api import get_arch
        >>> arch = get_arch('msp430')
        >>> arch
        msp430-arch
        >>> type(arch)
        <class 'ppci.arch.msp430.arch.Msp430Arch'>
    """
    if isinstance(arch, Architecture):
        return arch
    elif isinstance(arch, str):
        # Horrific import cycle created. TODO: restructure this
        from .target_list import create_arch
        if ':' in arch:
            # We have target with options attached
            parts = arch.split(':')
            return create_arch(parts[0], options=tuple(parts[1:]))
        else:
            return create_arch(arch)
    raise ValueError('Invalid architecture {}'.format(arch))


__all__ = ['Architecture', 'Frame', 'Isa', 'get_arch', 'get_current_arch']
