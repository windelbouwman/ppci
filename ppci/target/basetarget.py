"""
  Base classes for defining a target
"""

import logging


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
        Meta class to make the creation of instructions less
        repetitive. This meta class automatically generates
        the following methods:
        __init__
        __repr__
    """
    def __init__(cls, name, bases, attrs):
        super(InsMeta, cls).__init__(name, bases, attrs)

        # Register instruction with isa:
        if hasattr(cls, 'isa'):
            cls.isa.instructions.append(cls)


class Instruction(metaclass=InsMeta):
    """ Base instruction class """
    def __init__(self, *args):
        """ Base instruction constructor. Takes an arbitrary amount of
            arguments and tries to fit them on the args or syntax fields
        """
        # Generate constructor from args:
        if hasattr(self, 'args'):
            formal_args = getattr(self, 'args')
        elif hasattr(self, 'syntax'):
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
        if len(self.tokens) > 0:
            setattr(self, 'token', self.tokens[0]())
        for x, ct in enumerate(self.tokens):
            setattr(self, 'token{}'.format(x + 1), ct())

    def _get_tp(self, st):
        pass

    def _get_repr(self, st):
        """ Get the repr of a syntax part. Can be str or int, in refering
            to an element in the args list """
        if type(st) is str:
            return st
        elif type(st) is int:
            arg = self.args[st][0]
            return str(getattr(self, arg))
        else:
            raise Exception()

    @classmethod
    def get_argclass(self, arg):
        """ Given an argument, determine its class """
        if type(arg) is int:
            return self.args[arg][1]
        elif type(arg) is InstructionProperty:
            return arg._cls
        else:
            raise NotImplementedError(str(arg))

    def __repr__(self):
        if hasattr(self, 'syntax'):
            return ' '.join(self._get_repr(st) for st in self.syntax)
        else:
            return super().__repr__()

    def encode(self):
        return bytes()

    def relocations(self):
        return []

    def symbols(self):
        return []

    def literals(self, add_literal):
        pass


class Nop(Instruction):
    """ Instruction that does nothing and has zero size """
    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


class PseudoInstruction(Instruction):
    pass


class Label(PseudoInstruction):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '{}:'.format(self.name)

    def symbols(self):
        return [self.name]


class Comment(PseudoInstruction):
    def __init__(self, txt):
        self.txt = txt

    def encode(self):
        return bytes()

    def __repr__(self):
        return '; {}'.format(self.txt)


class Alignment(PseudoInstruction):
    def __init__(self, a):
        self.align = a

    def __repr__(self):
        return 'ALIGN({})'.format(self.align)

    def encode(self):
        pad = []
        # TODO
        address = 0
        while (address % self.align) != 0:
            address += 1
            pad.append(0)
        return bytes(pad)


class Register:
    def __init__(self, name):
        self.name = name

    def __gt__(self, other):
        return self.num > other.num


class InstructionProperty(property):
    """ Custom derived property that implements the descriptor protocol
        by inheriting property
    """
    def __init__(self, name, cls, getter, setter):
        self._name = name
        self._cls = cls
        super().__init__(getter, setter)


def register_argument(name, cls):
    """ Create a property for an instruction. When an instruction has
        an register parameter, use this function to create the property.
        The name is the name that will be shown in the usage.
        The cls is the type of register that this function must take.
    """
    # Construct a private backing field for the property:
    private_field = '_{}'.format(name)

    def getter(self):
        return getattr(self, private_field)

    def setter(self, value):
        assert isinstance(value, cls)
        setattr(self, private_field, value)

    return InstructionProperty(name, cls, getter, setter)


def value_argument(name):
    # Construct a private backing field for the property:
    return register_argument(name, int)


class Target:
    def __init__(self, name, desc=''):
        logging.getLogger().info('Creating {} target'.format(name))
        self.name = name
        self.desc = desc
        self.registers = []
        self.byte_sizes = {'int': 4}  # For front end!
        self.byte_sizes['byte'] = 1

    def __repr__(self):
        return '{}-target'.format(self.name)

    def lower_frame_to_stream(self, frame, outs):
        """ Lower instructions from frame to output stream """
        for im in frame.instructions:
            if isinstance(im.assem, Instruction):
                outs.emit(im.assem)
            else:
                assert isinstance(im.assem, InsMeta)
                # Construct the instruction with from_im method:
                ins = im.assem.from_im(im)
                outs.emit(ins)

    def add_reloc(self, name, f):
        self.reloc_map[name] = f
