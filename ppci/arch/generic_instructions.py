from .encoding import Instruction


class VirtualInstruction(Instruction):
    """ Virtual instruction.

    Virtual instructions are instructions used during code generation
    and can never be encoded into a stream.
    """

    def encode(self):  # pragma: no cover
        raise RuntimeError('Cannot encode virtual {}'.format(self))


class ArtificialInstruction(VirtualInstruction):
    """ This is an artificial instruction.

    It is actually more a macro, when emitted, the render function is
    called """

    def render(self):  # pragma: no cover
        """ Implement this by generating a sequence of actual instructions """
        raise NotImplementedError()


class PseudoInstruction(Instruction):
    """ Pseudo instruction.

    Pseudo instructions can be emitted into a stream, but are not real
    machine instructions. They are instructions like comments, labels
    and debug information alike information.
    """

    def __init__(self):
        super().__init__()

    def encode(self):
        return bytes()


class Nop(Instruction):
    """ Instruction that does nothing and has zero size """

    def encode(self):
        return bytes()

    def __repr__(self):
        return 'NOP'


class RegisterUseDef(VirtualInstruction):
    """ Magic instruction that can be used to define and use registers """

    def __init__(self, uses=(), defs=()):
        super().__init__()
        self.add_uses(uses)
        self.add_defs(defs)

    def __repr__(self):
        return 'VUseDef'

    def add_use(self, reg):
        self.extra_uses.append(reg)

    def add_uses(self, uses):
        for use in uses:
            self.add_use(use)

    def add_def(self, reg):
        self.extra_defs.append(reg)

    def add_defs(self, defs):
        for df in defs:
            self.add_def(df)


class Comment(PseudoInstruction):
    """ Assembly language comment """

    def __init__(self, comment):
        super().__init__()
        self.comment = comment

    def __repr__(self):
        return '; {}'.format(self.comment)


class Label(PseudoInstruction):
    """ Assembly language label instruction """

    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '{}:'.format(self.name)

    def symbols(self):
        return [self.name]


class Alignment(PseudoInstruction):
    """ Instruction to indicate alignment.

    Encodes to nothing, but is
    used in the linker to enforce multiple of x byte alignment
    """

    def __init__(self, a, rep=None):
        super().__init__()
        self.align = a
        self.rep = rep

    def __repr__(self):
        if self.rep:
            return self.rep
        else:
            return 'ALIGN({})'.format(self.align)


class SectionInstruction(PseudoInstruction):
    """ Select a certain section to emit output into. """

    def __init__(self, a, rep=None):
        super().__init__()
        self.name = a
        self.rep = rep

    def __repr__(self):
        if self.rep:
            return self.rep
        else:
            return 'section {}'.format(self.name)


class DebugData(PseudoInstruction):
    """ Carrier instruction of debug information. """

    def __init__(self, data):
        super().__init__()
        self.data = data

    def __repr__(self):
        return '.debug_data( {} )'.format(self.data)
