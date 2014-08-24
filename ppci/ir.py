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
        # Link entry to epilog:
        self.entry.extra_successors.append(self.epiloog)

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

    def add_parameter(self, p):
        assert type(p) is Parameter
        p.num = len(self.arguments)
        self.arguments.append(p)
        # p.parent = self.entry


class Block:
    """
        Uninterrupted sequence of instructions with a label at the start.
    """
    def __init__(self, name, function=None):
        self.name = name
        self.function = function
        self.instructions = []
        self.extra_successors = []

    parent = property(lambda s: s.function)

    def __repr__(self):
        return '{0}:'.format(self.name)

    def insert_instruction(self, i):
        """ Insert an instruction at the front of the block """
        i.parent = self
        self.instructions.insert(0, i)

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

    def remove_instruction(self, i):
        """ Remove instruction from block """
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
            return self.LastInstruction.Targets + self.extra_successors
        return [] + self.extra_successors

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

    def dominates(self, other):
        cfg_info = self.function.cfg_info
        return cfg_info.strictly_dominates(self, other)


def VarUse(name):
    """ Creates a property that also keeps track of usage """
    def getter(self):
        if name in self.var_map:
            return self.var_map[name]
        else:
            return "Not set!"

    def setter(self, value):
        # If value was already set, remove usage
        if name in self.var_map:
            self.del_use(self.var_map[name])
        # Place the value in the var map:
        self.var_map[name] = value

        # Add usage:
        self.add_use(value)
    return property(getter, setter)


# Instructions:
class Instruction:
    """ Base class for all instructions that go into a basic block """
    def __init__(self):
        # Create a collection to store the values this value uses.
        # TODO: think of better naming..
        self.var_map = {}
        self.parent = None
        self.uses = set()

    @property
    def block(self):
        return self.parent

    def add_use(self, v):
        """ Add v to the list of values used by this instruction """
        assert isinstance(v, Value)
        self.uses.add(v)
        v.add_user(self)

    def del_use(self, v):
        assert isinstance(v, Value)
        self.uses.remove(v)
        v.del_user(self)

    def replace_use(self, old, new):
        # TODO: update reference
        assert old in self.var_map.values()
        for name in self.var_map:
            if self.var_map[name] is old:
                self.del_use(old)
                self.var_map[name] = new
                self.add_use(new)

    def remove_from_block(self):
        for use in list(self.uses):
            self.del_use(use)
        self.block.remove_instruction(self)

    def dominates(self, other):
        """ Checks if this instruction dominates another instruction """
        if type(self) is Parameter or type(self) is GlobalVariable:
            # TODO: hack, parameters dominate all other instructions..
            return True
        # All other instructions must have a containing block:
        assert self.block is not None, '{} has no block'.format(self)

        # Phis are special case:
        if type(other) is Phi:
            # TODO: hack, return True for now!!
            for block in other.inputs:
                if other.inputs[block] == self:
                    # This is the queried dominance branch
                    # Check if this instruction dominates the last instruction of this block
                    return self.dominates(block.LastInstruction)
            raise Exception('Cannot query dominance for this phi')
        # For all other instructions follow these rules:
        if self.block == other.block:
            block = self.block
            return block.instructions.index(self) < block.instructions.index(other)
        else:
            return self.block.dominates(other.block)

    @property
    def IsTerminator(self):
        return isinstance(self, LastStatement)


class Value(Instruction):
    """ An instruction that results in a value has a type and a name """
    def __init__(self, name, ty):
        super().__init__()
        assert isinstance(ty, Typ)
        self.name = name
        self.ty = ty
        self.used_by = set()

    def add_user(self, i):
        """ Add a usage for this value """
        self.used_by.add(i)

    def del_user(self, i):
        """ Add a usage for this value """
        self.used_by.remove(i)

    def used_in_blocks(self):
        """ Returns a set of blocks where this value is used """
        return set(i.block for i in self.used_by)

    @property
    def is_used(self):
        return bool(len(self.used_by))

    @property
    def use_count(self):
        return len(self.used_by)

    def replace_by(self, value):
        """ Replace all uses of this value by another value """
        for use in list(self.used_by):
            use.replace_use(self, value)


class Expression(Value):
    """ Base class for an expression """
    pass


class Undefined(Value):
    def __repr__(self):
        return '{} = Undef'.format(self.name)


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
        for arg in self.arguments:
            self.add_use(arg)

    def replace_use(self, old, new):
        raise NotImplementedError()

    def __repr__(self):
        args = ', '.join(arg.name for arg in self.arguments)
        return '{} = {}({})'.format(self.name, self.f, args)


# Data operations
class Binop(Expression):
    """ Generic binary operation """
    ops = ['+', '-', '*', '/', '|', '&', '<<', '>>']
    a = VarUse('a')
    b = VarUse('b')

    def __init__(self, a, operation, b, name, ty):
        super().__init__(name, ty)
        assert operation in Binop.ops
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


class Phi(Value):
    """ Imaginary phi instruction to make SSA possible. """
    def __init__(self, name, ty):
        super().__init__(name, ty)
        self.inputs = {}

    def __repr__(self):
        inputs = {b: v.name for b,v in self.inputs.items()}
        return '{} = Phi {}'.format(self.name, inputs)

    def replace_use(self, old, new):
        raise NotImplementedError()

    def set_incoming(self, block, value):
        if block in self.inputs:
            self.del_use(self.inputs[block])
        self.inputs[block] = value
        self.add_use(value)


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
    address = VarUse('address')
    def __init__(self, address, name, ty):
        super().__init__(name, ty)
        self.address = address

    def __repr__(self):
        return '{} = [{}]'.format(self.name, self.address.name)


class Store(Instruction):
    """ Store a value into memory """
    address = VarUse('address')
    value = VarUse('value')
    def __init__(self, value, address):
        super().__init__()
        self.address = address
        self.value = value

    def __repr__(self):
        return '[{}] = {}'.format(self.address.name, self.value.name)


class Addr(Expression):
    """ Address of label """
    e = VarUse('e')
    def __init__(self, e, name, ty):
        super().__init__(name, ty)
        self.e = e

    def __repr__(self):
        return '{} = &{}'.format(self.name, self.e.name)


# Branching:
class LastStatement(Instruction):
    def __init__(self):
        super().__init__()

    def changeTarget(self, old, new):
        idx = self.Targets.index(old)
        self.Targets[idx] = new


class Terminator(LastStatement):
    """ Instruction that terminates the terminal block """
    def __init__(self):
        super().__init__()
        self.Targets = []

    def __repr__(self):
        return 'Terminator'


class Jump(LastStatement):
    """ Jump statement to some target location """
    def __init__(self, target):
        super().__init__()
        self.Targets = [target]

    def setTarget(self, t):
        self.Targets[0] = t

    target = property(lambda s: s.Targets[0], setTarget)

    def __repr__(self):
        return 'JUMP {}'.format(self.target.name)


class CJump(LastStatement):
    """ Conditional jump to true or false labels. """
    conditions = ['==', '<', '>', '>=', '<=', '!=']
    a = VarUse('a')
    b = VarUse('b')

    def __init__(self, a, cond, b, lab_yes, lab_no):
        super().__init__()
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
