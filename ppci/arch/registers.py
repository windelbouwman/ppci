class Register:
    """ Baseclass of all registers types """

    # TODO: __slots__ = ('name', '_num', '_color')

    @classmethod
    def all_registers(cls):
        """ Return all possible instances for this class """
        if hasattr(cls, "registers"):
            return getattr(cls, "registers")
        else:  # pragma: no cover
            raise NotImplementedError()

    def __init__(self, name, num=None, aliases=(), aka=()):
        assert isinstance(name, str)
        self.name = name
        if num is None:
            self._color = None
        else:
            assert isinstance(num, int)
            self._color = num

        self._num = num

        # If this register interferes with another register:
        self.aliases = aliases
        self.aka = aka

    def __repr__(self):
        if self._num is None:
            if self.is_colored:
                reg = self.from_num(self.color)
            else:
                reg = "-"
            return "{}[{}]".format(self.name, reg)
        else:
            return self.name

    def __str__(self):
        if self._num is None:
            if self.is_colored:
                return self.from_num(self.color).name
            else:
                return self.name
        else:
            return self.name

    def get_real(self):
        """ Retrieve the real hardware register.

        If this is a virtual register, return it's num.
        """
        if self._num is None:
            return self.from_num(self._color)
        else:
            return self

    @classmethod
    def from_num(cls, num):
        """ Retrieve the singleton instance of the given
        register number. """
        raise NotImplementedError()

    @property
    def num(self):
        """ When the register is colored, this property can be used """
        if self._num is None:
            assert self.is_colored
            return self._color
        else:
            return self._num

    @property
    def color(self):
        """ The coloring of this register """
        return self._color

    def set_color(self, color):
        self._color = color

    @property
    def is_colored(self):
        """ Determine whether the register is colored """
        return self._color is not None


class RegisterClass:
    __slots__ = ('name', 'ir_types', 'typ', 'registers')

    def __init__(self, name, ir_types, typ, registers):
        self.name = name
        self.ir_types = ir_types
        self.typ = typ
        assert issubclass(typ, Register)
        self.registers = registers
