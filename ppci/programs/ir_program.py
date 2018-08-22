
from io import StringIO

from .. import irutils

from .base import IntermediateProgram

from ..ir import Module as IrModule
from ..wasm import ir_to_wasm
from ..api import ir_to_object, get_arch, optimize

from ..lang.python import ir_to_python


class IrProgram(IntermediateProgram):
    """ PPCI IR code is the intermediate representation used in PPCI.
    """

    def _check_items(self, items):
        for item in items:
            assert isinstance(item, IrModule)
        return items

    def _copy(self):
        raise NotImplementedError()

    def _get_report(self, html):

        pieces = []
        for m in self.items:
            f = StringIO()
            irutils.Writer(f).write(m, verify=False)
            pieces.append(f.getvalue())
        return '\n\n==========\n\n'.join(pieces)

    def optimize(self, level=2):
        """ Optimize the ir program """
        for item in self.items:
            optimize(item, level=level)

    def to_x86(self, **options):
        """ Compile to X86 machine code.

        Status: ...
        """

        if options.get('win', ''):
            arch = get_arch('x86_64:wincc')
        else:
            arch = get_arch('x86_64')

        # todo: don't we want to be able to pass debug_db here?
        ppci_modules = [m for m in self.items]
        if self.debugdb:
            ob = ir_to_object(ppci_modules, arch, debug=True)
        else:
            ob = ir_to_object(ppci_modules, arch, debug=False)

        return self._new('x86', [ob])

    def to_arm(self, **options):
        """ Compile to ARM machine code.

        Status: ...
        """
        arch = get_arch('arm')

        # todo: don't we want to be able to pass debug_db here?
        ppci_modules = [m for m in self.items]
        if self.debugdb:
            ob = ir_to_object(ppci_modules, arch, debug=True)
        else:
            ob = ir_to_object(ppci_modules, arch, debug=False)

        return self._new('arm', [ob])

    def to_python(self, **options):
        """ Compile PPCI IR to Python. Not very efficient or pretty code,
        but it can be useful to test the IR code without compiling to machine
        code.

        Status: complete: can compile the full IR spec.
        """

        # pieces = []
        # for m in self.items:
        #
        #     pythonizer = ir_to_python.IrToPython(f)
        #     pythonizer.header()
        #     pythonizer.generate(m)
        #     py_code = f.getvalue()
        #     pieces.append(py_code)

        f = StringIO()
        ir_to_python(self.items, f)
        code = f.getvalue()

        return self._new('python', [code])

    def to_wasm(self, **options):
        """ Compile PPCI IR to WASM.

        Do this by taking each ir module into a wasm module.
        """
        return self._new('wasm', [ir_to_wasm(c) for c in self.items])
