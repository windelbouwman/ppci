""" Code to load a class file compiled to native code in python memory space.
"""

import logging

from .io import read_class_file
from .class2ir import class_to_ir


def load_class(filename):
    """ Load a compiled class into memory.
    """
    logger = logging.getLogger("jvm.io")
    with open(filename, "rb") as f:
        class_file = read_class_file(f)

    ir_module = class_to_ir(class_file)

    from ...api import ir_to_object, get_current_arch

    arch = get_current_arch()
    logger.info("Instantiating class as %s code", arch)
    obj = ir_to_object([ir_module], arch, debug=True)

    from ...utils.codepage import load_obj

    _code_module = load_obj(obj)
    return _code_module
