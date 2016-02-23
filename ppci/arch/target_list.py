
"""
    Contains a list of instantiated targets.
"""

from functools import lru_cache
from .arm import ArmArch
from .avr import AvrArch
from .msp430 import Msp430Arch
from .x86_64 import X86_64Arch
from .mos6500 import Mos6500Target
from .riscv import RiscvTarget


target_classes = [
    ArmArch,
    AvrArch,
    Mos6500Target,
    Msp430Arch,
    RiscvTarget,
    X86_64Arch]


target_class_map = {t.name: t for t in target_classes}
target_names = tuple(sorted(target_class_map.keys()))


@lru_cache(maxsize=30)
def get_arch(name, options=None):
    """ Get a target architecture by its name. Possibly arch options can be
        given.
    """
    # Create the instance!
    target = target_class_map[name](options=options)
    return target
