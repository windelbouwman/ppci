import types
import logging

"""
  Base classes for defining a target
"""


class Isa:
    def __init__(self):
        self.lower_funcs = {}
        self.instructions = []
        self.typ2nt = {}

    def register_instruction(self, i):
        self.instructions.append(i)


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
        # print('META init', name, bases, attrs)

        # Generate constructor from args:
        if hasattr(cls, 'args'):
            formal_args = getattr(cls, 'args')

            def _init_(self, *args):
                # Construct token:
                setattr(self, 'token', cls.tokens[0]())

                # Set parameters:
                assert len(args) == len(formal_args)
                for fa, a in zip(formal_args, args):
                    assert isinstance(a, fa[1]), '{}!={}'.format(a, fa[1])
                    setattr(self, fa[0], a)
            setattr(cls, '__init__', _init_)

        # Define repr method:
        if hasattr(cls, 'syntax'):
            pass
            # Register assembler rule:

        # Register lowering functions:
        if hasattr(cls, 'from_im'):
            cls.isa.lower_funcs[cls] = cls.from_im

        # Register instruction with isa:
        if hasattr(cls, 'isa'):
            cls.isa.register_instruction(cls)


class Instruction(metaclass=InsMeta):
    """ Base instruction class """
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


class Target:
    def __init__(self, name, desc=''):
        logging.getLogger().info('Creating {} target'.format(name))
        self.name = name
        self.desc = desc
        self.registers = []
        self.byte_sizes = {'int': 4}  # For front end!
        self.byte_sizes['byte'] = 1

        # For lowering:
        self.lower_functions = {}

    def __repr__(self):
        return '{}-target'.format(self.name)

    def lower_frame_to_stream(self, frame, outs):
        """ Lower instructions from frame to output stream """
        for im in frame.instructions:
            if isinstance(im.assem, Instruction):
                outs.emit(im.assem)
            else:
                # TODO assert isinstance(Abs
                ins = self.lower_functions[im.assem](im)
                outs.emit(ins)

    def add_lowering(self, cls, f):
        """ Add a function to the table of lowering options for this target """
        self.lower_functions[cls] = f

    def add_reloc(self, name, f):
        self.reloc_map[name] = f
