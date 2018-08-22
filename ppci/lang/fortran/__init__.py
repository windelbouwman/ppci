""" This is the fortran frontend.

Currently this front-end is a work in progress.

"""

from .parser import FortranParser
from .utils import Visitor, Printer


class FortranBuilder:
    def __init__(self):
        self.parser = FortranParser()

    def build(self, src):
        ast = self.parser.parse(src)
        mods = []
        ast
        return mods


def fortran_to_ir(source):
    """ Translate fortran source into IR-code """
    builder = FortranBuilder()
    ir_modules = builder.build(source)
    return ir_modules


__all__ = ['fortran_to_ir', 'FortranParser', 'Visitor', 'Printer']
