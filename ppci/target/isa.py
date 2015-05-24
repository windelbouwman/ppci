"""
Isa related classes.
These can be used to define an instruction set.

"""


class Register:
    """ Baseclass of all registers types """
    def __init__(self, name, num=None):
        assert type(name) is str
        self.name = name
        self._num = num

    def __repr__(self):
        return 'reg_{}'.format(self.name)

    @property
    def num(self):
        """ When the register is colored, this property can be used """
        assert self.is_colored
        return self._num

    @property
    def color(self):
        return self._num

    def set_color(self, color):
        self._num = color

    @property
    def is_colored(self):
        return self.color is not None


class InstructionProperty(property):
    """ Custom derived property that implements the descriptor protocol
        by inheriting property
    """
    def __init__(
            self, name, cls, getter, setter, read=False, write=False,
            default_value=None):
        self._name = name
        self._cls = cls
        self._read = read
        self._write = write
        self._default_value = default_value
        super().__init__(getter, setter)

    def __repr__(self):
        return 'property name={}, cls={}'.format(self._name, self._cls)


class RegisterProperty(InstructionProperty):
    pass


def register_argument(name, cls, read=False, write=False, default_value=None):
    """ Create a property for an instruction. When an instruction has
        an register parameter, use this function to create the property.
        The name is the name that will be shown in the usage.
        The cls is the type of register that this function must take.
    """
    # Construct a private backing field for the property:
    private_field = '_{}'.format(name)

    if issubclass(cls, Register):
        assert read or write

    def getter(self):
        return getattr(self, private_field)

    def setter(self, value):
        assert isinstance(value, cls)
        setattr(self, private_field, value)

    return InstructionProperty(
        name, cls, getter, setter,
        read=read, write=write, default_value=default_value)


def value_argument(name):
    # Construct a private backing field for the property:
    return register_argument(name, int)


class Isa:
    """
        Container type for an instruction set.
        Contains a list of instructions, mappings from intermediate code
        to instructions.

        Isa's can be merged into new isa's which can be used to define target.
        For example the arm without FPU can be combined with the FPU isa
        to expand the supported functions.
    """
    def __init__(self):
        self.instructions = []
        self.typ2nt = {}

    def register_instruction(self, i):
        """ Register an instruction into this ISA """
        self.instructions.append(i)

    def calc_kws(self):
        """ Calculate which keywords are used in assembler syntax """
        kws = set()
        for i in self.instructions:
            if hasattr(i, 'syntax'):
                for s in i.syntax:
                    if type(s) is str and s.isalnum():
                        kws.add(s)
        return kws


class InsMeta(type):
    """
        Meta class to register an instruction within an isa class.
    """
    def __init__(cls, name, bases, attrs):
        super(InsMeta, cls).__init__(name, bases, attrs)

        # Register instruction with isa:
        if hasattr(cls, 'isa'):
            assert isinstance(cls.isa, Isa)
            cls.isa.register_instruction(cls)


class Instruction(metaclass=InsMeta):
    """ Base instruction class. Instructions are automatically added to an
        isa object. Instructions are created in the following ways:
        - From python code, by using the instruction directly:
            self.stream.emit(Mov(r1, r2))
        - By the assembler. This is done via a generated parser.
        - By the instruction selector. This is done via pattern matching rules

        Instructions can then be emitted to output streams.
    """
    def __init__(self, *args, **kwargs):
        """ Base instruction constructor. Takes an arbitrary amount of
            arguments and tries to fit them on the args or syntax fields
        """
        # Generate constructor from args:
        if hasattr(self, 'syntax'):
            formal_args = []
            for st in self.syntax:
                if type(st) is InstructionProperty:
                    formal_args.append((st._name, st._cls))
        else:
            formal_args = None

        if formal_args is not None:
            # Set parameters:
            assert len(args) == len(formal_args)
            for fa, a in zip(formal_args, args):
                assert isinstance(a, fa[1]), '{}!={}'.format(a, fa[1])
                setattr(self, fa[0], a)

        # Construct token:
        if hasattr(self, 'tokens'):
            if len(self.tokens) > 0:
                setattr(self, 'token', self.tokens[0]())
            for position, token_cls in enumerate(self.tokens):
                setattr(self, 'token{}'.format(position + 1), token_cls())

        # Initialize the jumps this instruction makes:
        self.jumps = []
        self.ismove = False

        # Set several properties:
        self.__dict__.update(kwargs)

    def _get_repr(self, st):
        """ Get the repr of a syntax part. Can be str or prop class,
            in refering to an element in the args list """
        if type(st) is str:
            return st
        elif type(st) is InstructionProperty:
            return str(st.__get__(self))
        else:  # pragma: no cover
            raise NotImplementedError(str(st))

    @property
    def properties(self):
        if not hasattr(self, 'syntax'):
            return
        for st in self.syntax:
            if type(st) is InstructionProperty:
                yield st

    @property
    def used_registers(self):
        """ Return a set of all registers used by this instruction """
        # TODO: fix this ugly override!!!
        if 'src' in self.__dict__:
            return self.__dict__['src']
        if '_src' in self.__dict__:
            return self.__dict__['_src']
        s = []
        for p in self.properties:
            if p._read:
                s.append(p.__get__(self))
        return s

    @property
    def defined_registers(self):
        """ Return a set of all defined registers """
        if 'dst' in self.__dict__:
            return self.__dict__['dst']
        if '_dst' in self.__dict__:
            return self.__dict__['_dst']
        s = []
        for p in self.properties:
            if p._write:
                s.append(p.__get__(self))
        return s

    @property
    def registers(self):
        for p in self.properties:
            if issubclass(p._cls, Register):
                yield p.__get__(self)

    @property
    def is_colored(self):
        """ Determine whether all registers of this instruction are colored """
        return all(reg.is_colored for reg in self.registers)

    def __repr__(self):
        if hasattr(self, 'syntax'):
            syntax = getattr(self, 'syntax')
            return ' '.join(self._get_repr(st) for st in syntax)
        else:
            return super().__repr__()

    # Interface methods:
    def encode(self):
        """ Encode the instruction into binary form """
        return bytes()

    def relocations(self):
        return []

    def symbols(self):
        return []

    def literals(self, add_literal):
        pass


class Syntax:
    """ Defines a syntax for an instruction or part of an instruction.
        The syntax is a list of syntax elements.

        Optionally, the new_func is set. When using this syntax to create
        the instruction, instead of the default constructor, this function
        is called.

        The set_props property can be used to set additional properties
        after creating the instruction.
    """
    def __init__(self, syntax, new_func=None, set_props=None):
        assert isinstance(syntax, list)
        self.syntax = syntax
        self.new_func = new_func
        self.set_props = set_props


