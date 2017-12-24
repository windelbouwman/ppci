import io

from .base import SourceCodeProgram

from ..lang.python import python_to_wasm, python_to_ir


class PythonProgram(SourceCodeProgram):
    """ Python is a dynamic programming language, which is popular due to
    its great balance between simpliciy and expressiveness, and a thriving
    community.

    The items in a PythonProgram are strings.
    """

    def _check_items(self, items):
        if len(items) != 1:
            raise ValueError('PythonProgram can currently only have one item.')
        for item in items:
            assert isinstance(item, str)
        return items

    def _copy(self):
        return PythonProgram(*[item for item in self.items],
                             previous=self.previous, debugdb=self.debugdb)

    def _get_report(self, html):
        return '\n\n## ==========\n\n'.join(self.items)

    def run(self, namespace=None):
        """ Run (i.e. exec()) the code in the current interpreter.
        """
        if namespace is None:
            namespace = {}
        if len(self.items) != 1:
            raise RuntimeError(
                'Can only run Python programs consisting of one file.')
        code = self.items[0]
        exec(code, namespace)

    def to_wasm(self):
        """ Compile Python to WASM.

        Status: can compile a subset of Python, and assumes all floats.
        """
        wasm_modules = [python_to_wasm(c) for c in self.items]
        return self._new('wasm', wasm_modules)

    def to_ir(self):
        """ Compile Python to PPCI IR.

        Status: very preliminary.
        """
        ir_modules = [python_to_ir(io.StringIO(c)) for c in self.items]
        return self._new('ir', ir_modules)
