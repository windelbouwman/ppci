from .base import MachineProgram


class X86Program(MachineProgram):
    """ Machine code for most common desktops and laptops.
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

    def as_object(self):
        """ Export as binary code object (bytes)
        """
        obj = self._items[0]
        return bytes(obj.get_section('code').data)

    def as_elf(self, filename):
        """ Export as elf file.
        """
        raise NotImplementedError()

    def as_exe(self, filename):
        """ Export as a system executable file.
        """
        raise NotImplementedError()
