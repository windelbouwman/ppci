from .base import MachineProgram


class ArmProgram(MachineProgram):
    """ Machine code for most mobile devices and e.g. the Raspberry Pi.
    """

    def _check_items(self, items):
        return items

    def _copy(self):
        raise NotImplementedError()

    def _get_report(self, html):
        obj = self._items[0]
        lines = []
        lines.append(repr(obj))
        for section in obj.sections:
            lines.append(repr(section))
        for symbol in obj.symbols:
            lines.append(repr(symbol))
        for reloc in obj.relocations:
            lines.append(repr(reloc))
        return '\n'.join(lines)

    # todo: does this make sense for arm?
    def as_object(self):
        """ Export as binary code object (bytes)
        """
        obj = self._items[0]
        return bytes(obj.get_section('code').data)
