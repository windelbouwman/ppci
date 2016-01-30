
"""
    Contains a list of instantiated targets.
"""

from functools import lru_cache
from .arm import ArmTarget
from .avr import AvrTarget
from .msp430 import Msp430Target
from .x86_64 import X86_64Target
from .mos6500 import Mos6500Target
from .riscv import RiscvTarget


target_classes = [
    ArmTarget,
    AvrTarget,
    Mos6500Target,
    Msp430Target,
    RiscvTarget,
    X86_64Target]


target_class_map = {t.name: t for t in target_classes}
target_names = tuple(sorted(target_class_map.keys()))


@lru_cache(maxsize=30)
def get_target(name, options=None):
    """ Get a target by its name. Possibly arch options can be given. """
    # Create the instance!
    target = target_class_map[name](options=options)
    return target
