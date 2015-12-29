
"""
    Contains a list of instantiated targets.
"""

from .arm import ArmTarget
from .avr import AvrTarget
from .thumb import ThumbTarget
from .msp430.msp430 import Msp430Target
from .x86.target import X86Target

# Instance:
arm_target = ArmTarget()
thumb_target = ThumbTarget()
x86target = X86Target()
msp430target = Msp430Target()
avr_target = AvrTarget()

target_list = [arm_target, thumb_target, msp430target, x86target, avr_target]
targets = {t.name: t for t in target_list}
target_names = tuple(targets.keys())


def get_target(name):
    return targets[name]
