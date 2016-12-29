
class Register:
    """ Baseclass of all registers types """

    @classmethod
    def all_registers(cls):
        """ Return all possible instances for this class """
        if hasattr(cls, 'registers'):
            return getattr(cls, 'registers')
        else:  # pragma: no cover
            raise NotImplementedError()

    def __init__(self, name, num=None, aliases=(), aka=()):
        assert isinstance(name, str)
        self.name = name
        self._num = num

        # If this register interferes with another register:
        self.aliases = aliases
        self.aka = aka
        if num is not None:
            assert isinstance(num, int)

    def __repr__(self):
        return '{}'.format(self.name)

    @property
    def num(self):
        """ When the register is colored, this property can be used """
        assert self.is_colored
        return self._num

    @property
    def color(self):
        """ The coloring of this register """
        return self._num

    def set_color(self, color):
        self._num = color

    @property
    def is_colored(self):
        """ Determine whether the register is colored """
        return self.color is not None


class RegisterClass:
    def __init__(self, name, ir_types, typ, registers):
        self.name = name
        self.ir_types = ir_types
        self.typ = typ
        assert issubclass(typ, Register)
        self.registers = registers
