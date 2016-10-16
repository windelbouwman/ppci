
""" This is the fortran frontend.

Currently this front-end is a work in progress.

.. autoclass:: ppci.lang.fortran.FortranBuilder

.. autoclass:: ppci.lang.fortran.parser.FortranParser

"""

from .parser import FortranParser
from .utils import Visitor, Printer


class FortranBuilder:
    def __init__(self):
        self.parser = FortranParser()

    def build(self, src):
        ast = self.parser.parse(src)
        mods = []
        gen(ast)
        return mods
