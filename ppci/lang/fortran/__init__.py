
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
