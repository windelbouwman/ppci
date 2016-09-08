""" This module deals with encoding and decoding of instructions """


from .registers import Register
from .token import TokenSequence


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
        super().__init__(getter, setter)

    def __repr__(self):
        return 'property name={}, cls={}'.format(self._name, self._cls)

    @property
    def is_constructor(self):
        if isinstance(self._cls, tuple):
            return True
        else:
            return issubclass(self._cls, Constructor)


def register_argument(name, cls, read=False, write=False):
    """ Create a property for an instruction.

    When an instruction has
    a parameter, use this function to create the property.

    Arguments:
        name: The name that will be shown in the usage.
        cls: The type that this function must take.
    """
    # Construct a private backing field for the property:
    private_field = '_{}'.format(name)

    if isinstance(cls, type) and issubclass(cls, Register):
        assert read or write

    def getter(self):
        return getattr(self, private_field)

    def setter(self, value):
        assert isinstance(value, cls)
        setattr(self, private_field, value)

    return InstructionProperty(
        name, cls, getter, setter,
        read=read, write=write)


class Constructor:
    """ Instruction, or part of an instruction.

    An instruction is a special subclass of a constructor. It is final
    , in other words, it cannot be used in Constructors. An instruction
    can also be materialized, where as constructors are parts of an
    instruction.
    A constructor can contain a syntax and can be initialized by using
    this syntax.
    """
    syntax = None
    patterns = ()

    def __init__(self, *args, **kwargs):
        # Generate constructor from args:
        if self.syntax:
            formal_args = self.syntax.get_formal_arguments()

            # Set parameters:
            if len(args) != len(formal_args):
                raise TypeError(
                    '{} arguments given, but expected {}'.format(
                        len(args), len(formal_args)))
            for farg, arg in zip(formal_args, args):
                if not isinstance(arg, farg._cls):  # pragma: no cover
                    # Create some nice looking error:
                    raise TypeError(
                        '{} expected {}, but got "{}" of type {}'.format(
                            type(self), farg._cls, arg, type(arg)))
                setattr(self, farg._name, arg)

        for pname, pval in kwargs.items():
            # print('\n\n\n===', pname, pval)
            setattr(self, pname, pval)

    def __repr__(self):
        if self.syntax:
            return self.syntax.render(self)
        else:
            return super().__repr__()

    def set_patterns(self, tokens):
        """ Fill tokens with the specified bit patterns """
        for pattern in self.patterns:
            value = pattern.get_value(self)
            assert isinstance(value, int), str(self) + str(value) + str(pattern)
            tokens.set_field(pattern.field, value)
        self.set_user_patterns(tokens)

    def set_user_patterns(self, tokens):
        """ This is the place for custom patterns """
        pass

    @classmethod
    def from_tokens(cls, tokens):
        """ Create this constructor from tokens """
        prop_map = {}

        # Fill patterns:
        for pattern in cls.patterns:
            v = tokens.get_field(pattern.field)
            if isinstance(pattern, FixedPattern):
                if v != pattern.value:
                    raise ValueError('Cannot decode {}'.format(cls))
            elif isinstance(pattern, VariablePattern):
                if issubclass(pattern.prop._cls, Register):
                    regs = pattern.prop._cls.all_registers()
                    reg_map = {r.num: r for r in regs}
                    prop_map[pattern.prop] = reg_map[v]
                else:
                    # TODO: assume int here!
                    prop_map[pattern.prop] = v
            else:  # pragma: no cover
                raise NotImplementedError(pattern)

        # Create constructors:
        fargs = cls.syntax.get_formal_arguments()
        for farg in fargs:
            if isinstance(farg._cls, tuple):
                options = farg._cls

                for sub_con in options:
                    try:
                        c = sub_con.from_tokens(tokens)
                        print(c)
                        prop_map[farg] = c
                    except ValueError as e:
                        print(e)

        # Instantiate:
        init_args = [prop_map[a] for a in fargs]
        return cls(*init_args)

    @property
    def properties(self):
        """ Return all properties available into this syntax """
        if not self.syntax:
            return []
        return self.syntax.get_formal_arguments()

    @property
    def leaves(self):
        """ recursively yield all properties used, expanding composite
        props.
        All properties and the objects on which those properties can be getted
        are returned.
        """
        for prop in self.properties:
            if prop.is_constructor:
                for propcls in prop.__get__(self).leaves:
                    yield propcls
            else:
                yield prop, self

    @property
    def non_leaves(self):
        """ Get all composite parts """
        yield self
        for prop in self.properties:
            if prop.is_constructor:
                s2 = prop.__get__(self)
                # yield s2
                for nl in s2.non_leaves:
                    yield nl


class InsMeta(type):
    """ Meta class to register an instruction within an isa class. """
    def __init__(cls, name, bases, attrs):
        super(InsMeta, cls).__init__(name, bases, attrs)

        # Register instruction with isa:
        if hasattr(cls, 'isa'):
            cls.isa.add_instruction(cls)

    def __add__(cls, other):
        assert isinstance(other, InsMeta)
        tokens = cls.tokens + other.tokens
        patterns = cls.patterns + other.patterns
        syntax = cls.syntax + other.syntax
        members = {
            'tokens': tokens,
            'patterns': patterns,
            'syntax': syntax}
        member_list = list(cls.__dict__.items())
        member_list += list(other.__dict__.items())
        for name, val in member_list:
            if isinstance(val, InstructionProperty):
                if name in members:  # pragma: no cover
                    raise ValueError('{} already defined!'.format(name))
                members[name] = val
        name = cls.__name__ + other.__name__
        return InsMeta(name, (Instruction,), members)


class Instruction(Constructor, metaclass=InsMeta):
    """ Base instruction class.

    Instructions are automatically added to an
    isa object. Instructions are created in the following ways:

    - From python code, by using the instruction directly:
      self.stream.emit(Mov(r1, r2))
    - By the assembler. This is done via a generated parser.
    - By the instruction selector. This is done via pattern matching rules

    Instructions can then be emitted to output streams.
    """
    def __init__(self, *args, **kwargs):
        """
            Base instruction constructor. Takes an arbitrary amount of
            arguments and tries to fit them on the args or syntax fields
        """
        super().__init__(*args)

        # Initialize the jumps this instruction makes:
        self.jumps = []
        self.ismove = False

        # TODO: some instructions, like call, use several registers.
        # Probably this can be handled better:
        self.extra_uses = []
        self.extra_defs = []

        # Set several properties:
        for k, v in kwargs.items():
            assert hasattr(self, k)
            setattr(self, k, v)

    @property
    def used_registers(self):
        """ Return a set of all registers used by this instruction """
        s = []
        for p, o in self.leaves:
            if p._read:
                s.append(p.__get__(o))
        s.extend(self.extra_uses)
        return s

    def reads_register(self, register):
        """ Check if this instruction reads the given register """
        return register in self.used_registers

    @property
    def defined_registers(self):
        """ Return a set of all defined registers """
        s = []
        for p, o in self.leaves:
            if p._write:
                s.append(p.__get__(o))
        s.extend(self.extra_defs)
        return s

    def writes_register(self, register):
        """ Check if this instruction writes the given register """
        return register in self.defined_registers

    @property
    def registers(self):
        """ Determine all registers used by this instruction """
        for p, o in self.leaves:
            if issubclass(p._cls, Register):
                yield p.__get__(o)

    def set_all_patterns(self, tokens):
        """ Look for all patterns and apply them to the tokens """
        assert hasattr(self, 'patterns')
        # self.set_patterns(tokens)
        for nl in self.non_leaves:
            nl.set_patterns(tokens)

    def replace_register(self, old, new):
        """ Replace a register usage with another register """
        for p, o in self.leaves:
            if issubclass(p._cls, Register):
                if p.__get__(o) is old:
                    p.__set__(o, new)

    def get_tokens(self):
        tokens = []
        for nl in self.non_leaves:
            if hasattr(nl, 'tokens'):
                tokens.extend([t() for t in nl.tokens])
        return TokenSequence(tokens)

    # Interface methods:
    def encode(self):
        """ Encode the instruction into binary form.

        returns bytes for this instruction.
        """

        tokens = self.get_tokens()
        self.set_all_patterns(tokens)
        return tokens.encode()

    @classmethod
    def decode(cls, data):
        """ Decode data into an instruction of this class """
        tokens = [tok_cls() for tok_cls in cls.tokens]
        tokens = TokenSequence(tokens)
        tokens.fill(data)
        return cls.from_tokens(tokens)

    def relocations(self):
        return []

    def symbols(self):
        return []


class Syntax:
    """ Defines a syntax for an instruction or part of an instruction.

    Arguments:
        syntax: a list of syntax elements.

        new_func: When using this syntax to create
        the instruction, instead of the default constructor, this function
        is called.

        set_props: The set_props property can be used to set additional
        properties after creating the instruction.
    """
    GLYPHS = [
        '@', '&', '#', '=', ',', '.', ':',
        '(', ')', '[', ']', '{', '}',
        '+', '-', '*']

    def __init__(self, syntax, priority=0):
        assert isinstance(syntax, (list, tuple))
        for element in syntax:
            if isinstance(element, str):
                if element.isidentifier():
                    if not element.islower():
                        raise TypeError(
                            'element "{}" must be lower case'.format(element))
                elif element.isspace():
                    pass
                elif element in self.GLYPHS:
                    pass
                else:  # pragma: no cover
                    raise TypeError('Invalid element "{}"'.format(element))
            elif isinstance(element, InstructionProperty):
                pass
            else:  # pragma: no cover
                raise TypeError('Element must be string or parameter')
        self.syntax = syntax
        self.priority = priority

    def __add__(self, other):
        assert isinstance(other, Syntax)
        assert self.priority == 0
        assert other.priority == 0
        syntax = self.syntax + other.syntax
        return Syntax(syntax)

    def __repr__(self):
        return '{}'.format(self.syntax)

    def get_formal_arguments(self):
        """ Get the sequence of properties that must be passed in """
        formal_args = []
        for syntax_element in self.syntax:
            if isinstance(syntax_element, InstructionProperty):
                formal_args.append(syntax_element)
        return formal_args

    def get_args(self):
        """ Return all non-whitespace elements """
        for element in self.syntax:
            if isinstance(element, str) and element.isspace():
                continue
            yield element

    def render(self, obj):
        """ Return this syntax formatted for the given object. """
        return ''.join(self._get_repr(e, obj) for e in self.syntax)

    @staticmethod
    def _get_repr(syntax_element, obj):
        """ Get the repr of a syntax part. Can be str or prop class,
            in refering to an element in the args list """
        if isinstance(syntax_element, str):
            return syntax_element
        elif isinstance(syntax_element, InstructionProperty):
            return str(syntax_element.__get__(obj))
        else:  # pragma: no cover
            raise NotImplementedError(str(syntax_element))


class BitPattern:
    """ Base bit pattern class. A bit mapping is a mapping of a field
        to a value of some kind.
    """
    def __init__(self, field):
        self.field = field

    def get_value(self, objref):  # pragma: no cover
        raise NotImplementedError('Implement this for your pattern')

    def set_value(self, value):  # pragma: no cover
        raise NotImplementedError('Implement this for your pattern')


class FixedPattern(BitPattern):
    """ Bind a field to a fixed value """
    def __init__(self, field, value):
        super().__init__(field)
        self.value = value

    def get_value(self, objref):
        return self.value


class VariablePattern(BitPattern):
    def __init__(self, field, prop, transform=None):
        super().__init__(field)
        self.prop = prop
        self.transform = transform

    def get_value(self, objref):
        v = self.prop.__get__(objref)
        if isinstance(v, Register):
            v = v.num
        if self.transform:
            v = self.transform[0](v)
        return v
