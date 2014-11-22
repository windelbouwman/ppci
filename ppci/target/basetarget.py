import types
import logging

"""
  Base classes for defining a target
"""


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
        print('META init', name, bases, attrs)

        # Generate constructor from args:
        if hasattr(cls, 'args'):
            formal_args = getattr(cls, 'args')

            def _init_(self, *args):
                assert len(args) == len(formal_args)
                setattr(self, 'token', cls.tokens[0]())
                for fa, a in zip(formal_args, args):
                    assert isinstance(a, fa[1])
                    setattr(self, fa[0], a)
            setattr(cls, '__init__', _init_)

        # Define repr method:
        if hasattr(cls, 'syntax'):
            syntax = getattr(cls, 'syntax')

            def _repr_(self):
                s2 = []
                for st in syntax:
                    if type(st) is str:
                        s2.append(st)
                    else:
                        s2.append(str(st))
                return ' '.join(s2)
            setattr(cls, '__repr__', _repr_)

            # Register assembler rule:


        # Register lowering functions:
        if hasattr(cls, 'from_im'):
            cls.isa.lower_funcs[cls] = cls.from_im


class Instruction(metaclass=InsMeta):
    """ Base instruction class """
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


class LabelAddress:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(self) is type(other) and self.name == other.name


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

        # For assembler:
        self.assembler_rules = []
        self.asm_keywords = []

        self.generate_base_rules()

    def __repr__(self):
        return '{}-target'.format(self.name)

    def generate_base_rules(self):
        # Base rules for constants:
        self.add_rule('imm32', ['val32'], lambda x: x[0].val)
        self.add_rule('imm32', ['imm16'], lambda x: x[0])

        self.add_rule('imm16', ['val16'], lambda x: x[0].val)
        self.add_rule('imm16', ['imm12'], lambda x: x[0])

        self.add_rule('imm12', ['val12'], lambda x: x[0].val)
        self.add_rule('imm12', ['imm8'], lambda x: x[0])

        self.add_rule('imm8', ['val8'], lambda x: x[0].val)
        self.add_rule('imm8', ['imm5'], lambda x: x[0])

        self.add_rule('imm5', ['val5'], lambda x: x[0].val)
        self.add_rule('imm5', ['imm3'], lambda x: x[0])

        self.add_rule('imm3', ['val3'], lambda x: x[0].val)

    def add_keyword(self, kw):
        self.asm_keywords.append(kw)

    def add_instruction(self, rhs, f):
        self.add_rule('instruction', rhs, f)

    def add_rule(self, lhs, rhs, f):
        if type(f) is int:
            f2 = lambda x: f
        else:
            f2 = f
        assert type(f2) in [types.FunctionType, types.MethodType]
        self.assembler_rules.append((lhs, rhs, f2))

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
