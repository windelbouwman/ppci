
from .base import IntermediateProgram

from ..irs.wasm import wasm_to_ir


class WasmProgram(IntermediateProgram):
    """ WASM (a.k.a. Web Assembly) is an open standard to represent
    code in a compact, low level format that can be easily converterted
    to machine code, and run fast as well as safe.

    Items in a WasmProgram are WasmModule objects.
    """

    def _check_items(self, items):
        # for item in items:
        #     assert isinstance(item, WasmModule)
        return items

    def _copy(self):
        return WasmProgram(*[item.copy() for item in self.items],
                           previous=self.previous, debugdb=self.debugdb)

    def _get_report(self, html):
        pieces = [m.to_text() for m in self.items]
        return '\n\n==========\n\n'.join(pieces)

    def as_hex(self):
        """ Turn into a hex representation (using either the byte representation
        or the text representation).
        Raises NotImplementedError if this program does not have a binary
        nor textual representation.
        """
        bb = self.as_bytes()
        i = 0
        line = 0
        lines = []
        while i < len(bb):
            ints = [hex(j)[2:].rjust(2, '0') for j in bb[i:i+16]]
            lines.append(str(line).rjust(8, '0') + ' '.join(ints))
            i += 16
            line += 1
        return '\n'.join(lines)

    def as_bytes(self):
        """ Convert to WASM binary representation.
        """
        pieces = [m.to_bytes() for m in self.items]
        return b'\n\n==========\n\n'.join(pieces)

    def to_ir(self, **options):
        """ Compile WASM to IR.

        Status: very basic.
        """

        # todo: cannot pass the debugdb here
        return self._new('ir', [wasm_to_ir(c) for c in self.items])
