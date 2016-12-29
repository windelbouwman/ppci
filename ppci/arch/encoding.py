""" This module deals with encoding and decoding of instructions """


from .registers import Register
from .token import TokenSequence


class Operand(property):
    """ An instruction operand.

    When an instruction has
    an operand, use this function to create the property.

    Arguments:
        name: The name that will be shown in the usage.
        cls: The type that this function must take.

    Custom derived property that implements the descriptor protocol
    by inheriting property
    """
    def __init__(self, name, cls, read=False, write=False):
        self._name = name
        if isinstance(cls, dict):
            self._value_map = cls
            cls = tuple(cls.keys())
        else:
            self._value_map = None
        self._cls = cls
        self._read = read
        self._write = write

        # if isinstance(cls, type) or isinstance(cls, tuple)

        # Construct a private backing field for the property:
        private_field = '_{}'.format(name)

        if isinstance(cls, type) and issubclass(cls, Register):
            assert read or write

        def getter(self):
            return getattr(self, private_field)

        def setter(self, value):
            assert isinstance(value, cls)
            setattr(self, private_field, value)

        super().__init__(getter, setter)

    def __repr__(self):
        return 'property name={}, cls={}'.format(self._name, self._cls)

    @property
    def is_constructor(self):
        """ Check if this is a simple type, or a choice for many types """
        if isinstance(self._cls, tuple):
            return True
        else:
            return issubclass(self._cls, Constructor)

    @property
    def source(self):
        """ Get the original """
        return self

    def get_value(self, objref):
        """ Get the numerical value of this property """
        val = self.__get__(objref)
        if isinstance(val, Register):
            val = val.num
        if self._value_map and not isinstance(val, int):
            val = self._value_map[type(val)]
        assert isinstance(val, int)
        return val

    def set_value(self, objref, value):
        """ Set the numeric value of this property """
        raise NotImplementedError()

    def from_value(self, value):
        """ Create the an object of the right type from the given value """
        if issubclass(self._cls, Register):
            regs = self._cls.all_registers()
            reg_map = {r.num: r for r in regs}
            return reg_map[value]
        else:
            # assume int here!
            return value


class Transform:
    """ Wrapper to transform the numeric value of a property """
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def forwards(self, val):  # pragma: no cover
        """ Implement the forward transform here """
        raise NotImplementedError()

    def backwards(self, val):  # pragma: no cover
        """ Implement the backward transform here """
        raise NotImplementedError()

    def get_value(self, obj):
        """ Get the numerical value of this property """
        val = self._wrapped.get_value(obj)
        return self.forwards(val)

    def from_value(self, value):
        value = self.backwards(value)
        return self._wrapped.from_value(value)

    @property
    def source(self):
        """ Get the original data source """
        return self._wrapped.source


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

    def __str__(self):
        """ Create a nice looking assembly string """
        if self.syntax:
            return self.syntax.render(self)
        else:
            return super().__str__()

    @staticmethod
    def dict_to_patterns(d):
        """ Create patterns from dictionary """
        if isinstance(d, dict):
            patterns = []
            for field, value in d.items():
                if isinstance(value, int):
                    patterns.append(FixedPattern(field, value))
                elif isinstance(value, (Operand, Transform)):
                    patterns.append(VariablePattern(field, value))
                else:  # pragma: no cover
                    raise NotImplementedError(str(value))
        else:
            patterns = d
        return patterns

    def set_patterns(self, tokens):
        """ Fill tokens with the specified bit patterns """
        for pattern in self.dict_to_patterns(self.patterns):
            value = pattern.get_value(self)
            assert isinstance(value, int), str(self) + str(value)
            tokens.set_field(pattern.field, value)
        self.set_user_patterns(tokens)

    def set_user_patterns(self, tokens):
        """ This is the place for custom patterns """
        pass

    @classmethod
    def from_tokens(cls, tokens):
        """ Create this constructor from tokens """
        prop_map = {}

        patterns = cls.dict_to_patterns(cls.patterns)

        # Fill patterns:
        for pattern in patterns:
            v = tokens.get_field(pattern.field)
            if isinstance(pattern, FixedPattern):
                if v != pattern.value:
                    raise ValueError('Cannot decode {}'.format(cls))
            elif isinstance(pattern, VariablePattern):
                prop_map[pattern.prop.source] = pattern.prop.from_value(v)
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
        """ Get all composite parts.

        This is a depth first loop.
        """
        yield self
        for prop in self.properties:
            if prop.is_constructor:
                s2 = prop.__get__(self)
                # yield s2
                for nl in s2.non_leaves:
                    yield nl

    def gen_relocations(self):
        """ Override this method to generate relocation information """
        return []


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
        p1 = cls.dict_to_patterns(cls.patterns)
        p2 = cls.dict_to_patterns(other.patterns)
        patterns = p1 + p2
        syntax = cls.syntax + other.syntax
        members = {
            'tokens': tokens,
            'patterns': patterns,
            'syntax': syntax}
        member_list = list(cls.__dict__.items())
        member_list += list(other.__dict__.items())
        for name, val in member_list:
            if isinstance(val, Operand):
                if name in members:  # pragma: no cover
                    raise ValueError('{} already defined!'.format(name))
                members[name] = val
        name = cls.__name__ + other.__name__
        return InsMeta(name, (Instruction,), members)


class Instruction(Constructor, metaclass=InsMeta):
    """ Base instruction class.

    Instructions are created in the following ways:

    - From python code, by using the instruction directly:
      self.stream.emit(Mov(r1, r2))
    - By the assembler. This is done via a generated parser.
    - By the instruction selector. This is done via pattern matching rules

    Instructions can then be emitted to output streams.

    Instruction classes are automatically added to an
    isa if they have an isa attribute.
    """
    def __init__(self, *args, **kwargs):
        """ Base instruction constructor.

        Takes an arbitrary amount of arguments and tries to fit them
        on the args or syntax fields.
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
        precodes = []
        tokens = []
        for nl in self.non_leaves:
            if hasattr(nl, 'tokens'):
                for tc in nl.tokens:
                    t = tc()
                    if t.Info.precode:
                        precodes.append(t)
                    else:
                        tokens.append(t)
        return TokenSequence(precodes + tokens)

    def get_positions(self):
        """ Calculate the positions in the byte stream of all parts """
        pos = 0
        positions = {}
        for nl in self.non_leaves:
            positions[nl] = pos
            if hasattr(nl, 'tokens'):
                tokens = getattr(nl, 'tokens')
                size = sum(t.Info.size for t in tokens) // 8
            else:
                size = 0
            pos += size
        return positions

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

    @classmethod
    def sizes(cls):
        """ Get possible encoding sizes in bytes """
        if hasattr(cls, 'tokens'):
            return [sum(t.size for t in cls.tokens) // 8]
        else:
            return []

    def relocations(self):
        """ Determine the total set of relocations for this instruction """
        relocs = []
        positions = self.get_positions()
        for nl, offset in positions.items():
            for reloc in nl.gen_relocations():
                relocs.append(reloc.shifted(offset))
        return relocs

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
            elif isinstance(element, Operand):
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
            if isinstance(syntax_element, Operand):
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
        elif isinstance(syntax_element, Operand):
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
    def __init__(self, field, prop):
        super().__init__(field)
        self.prop = prop

    def get_value(self, objref):
        return self.prop.get_value(objref)


class Relocation:
    """ Baseclass for all relocation types.

    Subclass this class to create custom relocations.
    Subclasses should add the following attributes:
    - name: the name used to refer to the relocation type.
    - number: the number that can be used to uniquely identify the relocation.
    - apply: a function that can be used to apply the relocation.
    - calc: a function that calculates the value for the relocation.
    """
    name = None
    number = None
    token = None
    field = None

    def __init__(self, symbol_name, offset=0, addend=0, section=None):
        self.symbol_name = symbol_name
        self.addend = addend
        self.section = section
        self.offset = offset

    def __eq__(self, other):
        s = (
            self.symbol_name, self.offset, type(self),
            self.section, self.addend)
        o = (
            other.symbol_name, other.offset, type(other),
            other.section, other.addend)
        return s == o

    def shifted(self, offset):
        """ Create a shifted copy of this relocation """
        return type(self)(
            self.symbol_name, offset=self.offset+offset,
            addend=self.addend, section=self.section)

    @classmethod
    def size(cls):
        """ Calculate the amount of bytes this relocation requires """
        assert cls.token.Info.size % 8 == 0
        return cls.token.Info.size // 8

    def apply(self, sym_value, data, reloc_value):
        """ Apply this relocation type given some parameters.

        This is the default implementation which stores the outcome of
        the calculate function into the proper token. """
        assert self.token is not None
        token = self.token.from_data(data)
        assert self.field is not None
        assert hasattr(token, self.field)
        setattr(token, self.field, self.calc(sym_value, reloc_value))
        return token.encode()

    def calc(self, sym_value, reloc_value):  # pragma: no cover
        """ Calculate the relocation """
        raise NotImplementedError()
