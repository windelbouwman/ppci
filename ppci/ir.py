"""
Intermediate representation (IR) code classes.
"""


def label_name(dut):
    """ Returns the assembly code label name """
    if isinstance(dut, Block):
        f = dut.function
        return label_name(f) + '_' + dut.name
    elif isinstance(dut, Function) or isinstance(dut, GlobalVariable):
        return label_name(dut.module) + '_' + dut.name
    elif isinstance(dut, Module):
        return dut.name
    else:
        raise NotImplementedError(str(dut) + str(type(dut)))


class Typ:
    """ Type representation """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


i32 = Typ('i32')
i8 = Typ('i8')


class Module:
    """ Container unit for variables and functions. """
    def __init__(self, name):
        self.name = name
        self.functions = []
        self.variables = []

    def __repr__(self):
        return 'module {0}'.format(self.name)

    def add_function(self, f):
        """ Add a function to this module """
        self.functions.append(f)
        f.module = self

    def add_variable(self, v):
        assert type(v) is GlobalVariable
        self.variables.append(v)
        v.module = self

    def get_variables(self):
        return self.variables

    Variables = property(get_variables)

    def get_functions(self):
        return self.functions

    Functions = property(get_functions)

    def find_function(self, name):
        for f in self.funcs:
            if f.name == name:
                return f
        raise KeyError(name)


class Function:
    """ Represents a function. """
    def __init__(self, name, module=None):
        self.name = name
        self.entry = Block('entry')
        self.entry.function = self
        self.epiloog = Block('epilog')
        self.epiloog.function = self
        self.epiloog.addInstruction(Terminator())
        self.arguments = []
        if module:
            module.add_function(self)

    def __repr__(self):
        args = ','.join(str(a) for a in self.arguments)
        return 'function i32 {}({})'.format(self.name, args)

    def add_block(self, bb):
        #self.bbs.append(bb)
        bb.function = self

    def removeBlock(self, bb):
        #self.bbs.remove(bb)
        bb.function = None

    def getBlocks(self):
        bbs = [self.entry]
        worklist = [self.entry]
        while worklist:
            b = worklist.pop()
            for sb in b.Successors:
                if sb not in bbs:
                    bbs.append(sb)
                    worklist.append(sb)
        bbs.remove(self.entry)
        if self.epiloog in bbs:
            bbs.remove(self.epiloog)
        bbs.insert(0, self.entry)
        bbs.append(self.epiloog)
        return bbs

    def findBasicBlock(self, name):
        for bb in self.bbs:
            if bb.name == name:
                return bb
        raise KeyError(name)

    Blocks = property(getBlocks)

    @property
    def Entry(self):
        return self.entry

    def check(self):
        for b in self.Blocks:
            b.check()

    def addParameter(self, p):
        assert type(p) is Parameter
        p.num = len(self.arguments)
        self.arguments.append(p)


class Block:
    """
        Uninterrupted sequence of instructions with a label at the start.
    """
    def __init__(self, name, function=None):
        self.name = name
        self.function = function
        self.instructions = []

    parent = property(lambda s: s.function)

    def __repr__(self):
        return '{0}:'.format(self.name)

    def addInstruction(self, i):
        i.parent = self
        assert not isinstance(self.LastInstruction, LastStatement)
        self.instructions.append(i)

    def replaceInstruction(self, i1, i2):
        idx = self.instructions.index(i1)
        i1.parent = None
        i1.delete()
        i2.parent = self
        self.instructions[idx] = i2

    def removeInstruction(self, i):
        i.parent = None
        #i.delete()
        self.instructions.remove(i)

    @property
    def Instructions(self):
        return self.instructions

    @property
    def LastInstruction(self):
        if not self.Empty:
            return self.instructions[-1]

    @property
    def Empty(self):
        return len(self.instructions) == 0

    @property
    def FirstInstruction(self):
        return self.instructions[0]

    def getSuccessors(self):
        if not self.Empty:
            return self.LastInstruction.Targets
        return []

    Successors = property(getSuccessors)

    def getPredecessors(self):
        preds = []
        for bb in self.parent.Blocks:
            if self in bb.Successors:
                preds.append(bb)
        return preds

    Predecessors = property(getPredecessors)

    def precedes(self, other):
        raise NotImplementedError()


# Instructions:
class Instruction:
    """ Base class for all instructions that go into a basic block """
    pass


class Value(Instruction):
    """ A value has a type and a name """
    def __init__(self, name, ty):
        assert isinstance(ty, Typ)
        self.name = name
        self.ty = ty


class User(Value):
    """ Value that uses other values """
    def __init__(self, name, ty):
        super().__init__(name, ty)
        # Create a collection to store the values this value uses.
        # TODO: think of better naming..
        self.uses = set()

    def add_use(self, v):
        assert isinstance(v, Value)
        self.uses.add(v)


class Expression(User):
    """ Base class for an expression """
    pass


class Const(Expression):
    """ Represents a constant value """
    def __init__(self, value, name, ty):
        super().__init__(name, ty)
        self.value = value

    def __repr__(self):
        return '{} = Const {}'.format(self.name, self.value)


class Call(Expression):
    """ Call a function with some arguments """
    def __init__(self, f, arguments, name, ty):
        super().__init__(name, ty)
        assert type(f) is str
        self.f = f
        self.arguments = arguments

    def __repr__(self):
        args = ', '.join(arg.name for arg in self.arguments)
        return '{} = {}({})'.format(self.name, self.f, args)


# Data operations
class Binop(Expression):
    """ Generic binary operation """
    ops = ['+', '-', '*', '/', '|', '&', '<<', '>>']

    def __init__(self, a, operation, b, name, ty):
        super().__init__(name, ty)
        assert operation in Binop.ops
        #assert type(value1) is type(value2)
        assert isinstance(a, Value), str(a)
        assert isinstance(b, Value), str(b)
        self.a = a
        self.b = b
        self.operation = operation

    def __repr__(self):
        a, b = self.a.name, self.b.name
        return '{} = {} {} {}'.format(self.name, a, self.operation, b)


def Add(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '+', b, name, ty)


def Sub(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '-', b, name, ty)


def Mul(a, b, name, ty):
    """ Multiply a by b """
    return Binop(a, '*', b, name, ty)


def Div(a, b, name, ty):
    """ Divide a in b pieces """
    return Binop(a, '/', b, name, ty)


def Phi(User):
    """ Imaginary phi instruction to make SSA possible. """
    def __init__(self, name, ty):
        super().__init__(name, ty)
        self.inputs = []

    def add_input(self, value, block):
        self.inputs.append((value, block))


class Alloc(Expression):
    """ Allocates space on the stack """
    def __init__(self, name, ty, num_elements=4):
        super().__init__(name, ty)
        # self.num_elements = num_elements
        self.amount = num_elements

    def __repr__(self):
        return '{} = Alloc {} bytes'.format(self.name, self.amount)


class Variable(Expression):
    def __init__(self, name, ty):
        super().__init__(name, ty)
        self.name = name

    def __repr__(self):
        return 'Var {}'.format(self.name)


class GlobalVariable(Variable):
    def __repr__(self):
        return 'Global {}'.format(self.name)


class Parameter(Variable):
    def __repr__(self):
        return 'Param {}'.format(self.name)


class Load(Value):
    """ Load a value from memory """
    def __init__(self, address, name, ty):
        super().__init__(name, ty)
        assert isinstance(address, Value)
        self.address = address

    def __repr__(self):
        return '{} = [{}]'.format(self.name, self.address.name)


class Store(Instruction):
    """ Store a value into memory """
    def __init__(self, value, address):
        assert isinstance(address, Value)
        assert isinstance(value, Value)
        self.address = address
        self.value = value

    def __repr__(self):
        return '[{}] = {}'.format(self.address.name, self.value.name)


class Addr(Expression):
    """ Address of label """
    def __init__(self, e, name, ty):
        super().__init__(name, ty)
        self.e = e

    def __repr__(self):
        return '{} = &{}'.format(self.name, self.e.name)


class Statement(Instruction):
    """ Base class for all instructions. """
    @property
    def IsTerminator(self):
        return isinstance(self, LastStatement)


# Branching:
class LastStatement(Statement):
    def changeTarget(self, old, new):
        idx = self.Targets.index(old)
        self.Targets[idx] = new


class Terminator(LastStatement):
    """ Instruction that terminates the terminal block """
    def __init__(self):
        self.Targets = []

    def __repr__(self):
        return 'Terminator'


class Jump(LastStatement):
    """ Jump statement to some target location """
    def __init__(self, target):
        self.Targets = [target]

    def setTarget(self, t):
        self.Targets[0] = t

    target = property(lambda s: s.Targets[0], setTarget)

    def __repr__(self):
        return 'JUMP {}'.format(self.target.name)


class CJump(LastStatement):
    """ Conditional jump to true or false labels. """
    conditions = ['==', '<', '>', '>=', '<=', '!=']

    def __init__(self, a, cond, b, lab_yes, lab_no):
        assert cond in CJump.conditions
        self.a = a
        self.cond = cond
        self.b = b
        self.Targets = [lab_yes, lab_no]

    lab_yes = property(lambda s: s.Targets[0])
    lab_no = property(lambda s: s.Targets[1])

    def __repr__(self):
        return 'IF {} {} {} THEN {} ELSE {}'\
               .format(self.a.name,
                       self.cond, self.b.name, self.lab_yes, self.lab_no)
