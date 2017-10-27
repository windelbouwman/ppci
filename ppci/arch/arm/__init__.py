"""
Arm machine specifics. The arm target has several options:

* thumb: enable thumb mode, emits thumb code

.. autoclass:: ppci.arch.arm.ArmArch

"""

from .arch import ArmArch
from .program import ArmProgram

__all__ = ['ArmArch', 'ArmProgram']
