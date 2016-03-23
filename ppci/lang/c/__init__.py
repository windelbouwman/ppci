"""
    C front end.
"""

from .parser import Parser
from .nodes import Printer


class CBuilder:
    """ C builder that converts C code into ir-code """
    def __init__(self, march):
        self.march = march
        self.parser = Parser()
        self.cgen = None

    def build(self, src):
        cu = self.parser.parse(src)
        # self.cgen.gen(s)
        # Printer().visit(cu)
