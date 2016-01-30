
"""
    Contains a list of instantiated targets.
"""

from .arm import ArmTarget
from .avr import AvrTarget
from .msp430.msp430 import Msp430Target
from .x86_64.target import X86Target
from .mos6500 import Mos6500Target
from .riscv import RiscvTarget

# Instance:
arm_target = ArmTarget()
x86_64target = X86Target()
msp430target = Msp430Target()
avr_target = AvrTarget()
mos6500 = Mos6500Target()
riscv_target = RiscvTarget()


target_list = [
    arm_target,
    msp430target,
    avr_target,
    mos6500,
    riscv_target,
    x86_64target]

targets = {t.name: t for t in target_list}
target_names = tuple(sorted(targets.keys()))


def get_target(name):
    """ Get a target by its name """
    if ':' in name:
        # We have target with options attached
        l = name.split(':')
        target = get_target(l[0])
        for option in l[1:]:
            if option.startswith('no-'):
                target.disable_option(option[3:])
            else:
                target.enable_option(option)
    else:
        target = targets[name]
        # Reset options:
        for option in target.options:
            target.disable_option(option)
    return target
