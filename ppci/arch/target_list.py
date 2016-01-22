
"""
    Contains a list of instantiated targets.
"""

from .arm import ArmTarget
from .avr import AvrTarget
from .thumb import ThumbTarget
from .msp430.msp430 import Msp430Target
from .x86_64.target import X86Target
from .mos6500 import Mos6500Target


# Instance:
arm_target = ArmTarget()
thumb_target = ThumbTarget()  # TODO: merge thumb into arm?
x86target = X86Target()
msp430target = Msp430Target()
avr_target = AvrTarget()
mos6500 = Mos6500Target()

target_list = [
    arm_target, thumb_target, msp430target, x86target, avr_target, mos6500]
targets = {t.name: t for t in target_list}
target_names = tuple(sorted(targets.keys()))


def get_target(name):
    return targets[name]
