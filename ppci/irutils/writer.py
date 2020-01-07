from .verify import verify_module
from .. import ir


IR_FORMAT_INDENT = 2


def print_module(module, file=None, verify=True):
    """ Print an ir-module as text """
    Writer(file=file).write(module, verify=verify)


class Writer:
    """ Write ir-code to file """

    def __init__(self, file=None, extra_indent=""):
        self.extra_indent = extra_indent
        self.file = file

    def _print(self, level, txt):
        indent = self.extra_indent + " " * (level * IR_FORMAT_INDENT)
        print(indent + txt, file=self.file)

    def write(self, module: ir.Module, verify=True):
        """ Write ir-code to file f """
        assert isinstance(module, ir.Module)
        if verify:
            verify_module(module)
        self._print(0, "{};".format(module))

        for external in module.externals:
            self._print(0, "")
            self._print(0, "{};".format(external))

        for variable in module.variables:
            self._print(0, "")
            self._print(0, str(variable))

        for function in module.functions:
            self._print(0, "")
            self.write_function(function)

    def write_function(self, function):
        self._print(0, "{} {{".format(function))
        for block in function.blocks:
            self._print(1, "{} {{".format(block))
            for ins in block:
                self._print(2, "{};".format(ins))
            self._print(1, "}")
            self._print(0, "")
        self._print(0, "}")
