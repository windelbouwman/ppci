
"""
    Contains a list of instantiated targets.
"""

from .arm import ArmTarget
from .thumb import ThumbTarget
from .msp430.msp430 import Msp430Target
from .x86.target_x86 import X86Target

# Instance:
arm_target = ArmTarget()
thumb_target = ThumbTarget()
x86target = X86Target()
msp430target = Msp430Target()

target_list = [arm_target, thumb_target, msp430target]
targets = {t.name: t for t in target_list}
targetnames = list(targets.keys())
