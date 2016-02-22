"""
Intermediate representation (IR) code classes.
"""

# pylint: disable=R0903

from binascii import hexlify


def label_name(dut):
    """ Returns the assembly code label name """
    if isinstance(dut, Block):
        function = dut.function
        return label_name(function) + '_' + dut.name
    elif isinstance(dut, Function) or isinstance(dut, Variable):
        return label_name(dut.module) + '_' + dut.name
    elif isinstance(dut, Module):
        return dut.name
    else:  # pragma: no cover
        raise NotImplementedError(str(dut) + str(type(dut)))


class Typ:
    """ Base class for all types """
    pass


class BuiltinType(Typ):
    """ Built in type representation """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


# The builtin types:
f64 = BuiltinType('f64')
i64 = BuiltinType('i64')
i32 = BuiltinType('i32')
i16 = BuiltinType('i16')
i8 = BuiltinType('i8')
ptr = BuiltinType('ptr')


class Module:
    """ Container unit for variables and functions. """
    def __init__(self, name):
        self.name = name
        self._functions = []
        self._variables = []

    def __repr__(self):
        return 'module {0}'.format(self.name)

    def add_function(self, function):
        """ Add a function to this module """
        assert isinstance(function, Function)
        self._functions.append(function)
        function.module = self

    def add_variable(self, variable):
        """ Add a variable to this module """
        assert isinstance(variable, Variable)
        self._variables.append(variable)
        variable.module = self

    def get_variables(self):
        """ Get all variables of this module """
        return self._variables

    variables = property(get_variables)

    def get_functions(self):
        """ Get all functions of this module """
        return self._functions

    functions = property(get_functions)

    def stats(self):
        """ Returns a string with statistic information such as block count """
        num_functions = len(self.functions)
        num_blocks = sum(len(f.blocks) for f in self.functions)
        num_instructions = sum(f.num_instructions() for f in self.functions)
        return "functions: {}, blocks: {}, instructions: {}" \
            .format(num_functions,
                    num_blocks,
                    num_instructions)


class Function:
    """ Represents a function. """
    def __init__(self, name, module=None):
        self._blocks = None

        # Variables used in uniquifying names:
        self.defined_names = {}
        self.unique_counter = 0
        self.name = name

        # Create first blocks:
        self.entry = Block('entry')
        self.add_block(self.entry)
        self.epilog = Block('epilog')
        self.add_block(self.epilog)
        self.epilog.add_instruction(Terminator())

        # TODO: fix this other way?
        # Link entry to epilog:
        self.entry.extra_successors.append(self.epilog)
        self.epilog.extra_preds.append(self.entry)

        # TODO: cfg info as a property?

        self.arguments = []
        if module:
            module.add_function(self)

    def __repr__(self):
        args = ', '.join('{} {}'.format(a.ty, a.name) for a in self.arguments)
        return 'function XXX {}({})'.format(self.name, args)

    def __iter__(self):
        """ Iterate over all blocks in this function """
        for block in self.blocks:
            yield block

    def make_unique_name(self, dut):
        """ Check if the name of the given dut is unique
            and if not make it so """
        orig_name = dut.name
        while dut.name in self.defined_names.keys():
            dut.name = '{}_{}'.format(orig_name, self.unique_counter)
            self.unique_counter += 1
        self.defined_names[dut.name] = dut

    def add_block(self, block):
        """ Add a block to this function """
        # self.bbs.append(bb)
        block.function = self

        self.make_unique_name(block)

        # Mark cache as invalid:
        self._blocks = None

    def remove_block(self, block):
        """ Remove a block from this function """
        # self.bbs.remove(bb)
        block.function = None

        # Mark cache as invalid:
        self._blocks = None

    def get_blocks(self):
        """ Get all the blocks contained in this function """
        # Use a cache:
        if self._blocks is None:
            bbs = [self.entry]
            worklist = [self.entry]
            while worklist:
                b = worklist.pop()
                for sb in b.successors:
                    if sb not in bbs:
                        bbs.append(sb)
                        worklist.append(sb)
            bbs.remove(self.entry)
            if self.epilog in bbs:
                bbs.remove(self.epilog)
            bbs.insert(0, self.entry)
            bbs.append(self.epilog)
            self._blocks = bbs
        return self._blocks

    blocks = property(get_blocks)

    @property
    def special_blocks(self):
        """ Return iterable of special blocks. For now the entry block and
            the epilog.
        """
        return (self.entry, self.epilog)

    def add_parameter(self, parameter):
        """ Add an argument to this function """
        assert isinstance(parameter, Parameter)
        parameter.num = len(self.arguments)
        self.arguments.append(parameter)
        # p.parent = self.entry

    def num_instructions(self):
        """ Count the number of instructions contained in this function """
        return sum(len(block) for block in self.blocks)


class FastList:
    """
        List drop-in replacement that supports cached index operation.
        So the first time the index is complexity O(n), the second time
        O(1). When the list is modified, the cache is cleared.
    """
    __slots__ = ['_items', '_index_map']

    def __init__(self):
        self._items = []
        self._index_map = {}

    def __iter__(self):
        return self._items.__iter__()

    def __len__(self):
        return self._items.__len__()

    def __getitem__(self, key):
        return self._items.__getitem__(key)

    def append(self, i):
        """ Append an item """
        self._index_map.clear()
        self._items.append(i)

    def insert(self, pos, i):
        """ Insert an item """
        self._index_map.clear()
        self._items.insert(pos, i)

    def remove(self, i):
        self._index_map.clear()
        self._items.remove(i)

    def index(self, i):
        """ Second time the lookup of index is done in O(1) """
        if i not in self._index_map:
            self._index_map[i] = self._items.index(i)
        return self._index_map[i]


class Block:
    """
        Uninterrupted sequence of instructions with a label at the start.
    """
    def __init__(self, name, function=None):
        self.name = name
        self.function = function
        self.instructions = FastList()
        self.extra_successors = []
        self.extra_preds = []
        self._preds = set()

    parent = property(lambda s: s.function)

    def __repr__(self):
        return '{0}:'.format(self.name)

    def __iter__(self):
        for instruction in self.instructions:
            yield instruction

    def __len__(self):
        return len(self.instructions)

    def unique_name(self, value):
        self.function.make_unique_name(value)

    def insert_instruction(self, instruction, before_instruction=None):
        """ Insert an instruction at the front of the block """
        if before_instruction is not None:
            assert self == before_instruction.block
            pos = before_instruction.position
        else:
            pos = 0
        instruction.parent = self
        self.instructions.insert(pos, instruction)
        if isinstance(instruction, Value):
            self.unique_name(instruction)

    def add_instruction(self, i):
        """ Add an instruction to the end of this block """
        i.parent = self
        assert not isinstance(self.last_instruction, LastStatement)
        self.instructions.append(i)
        if isinstance(i, Value) and self.function is not None:
            self.unique_name(i)
        if isinstance(i, Return):
            self.function.epilog._preds.add(i)

    def replaceInstruction(self, i1, i2):
        idx = self.instructions.index(i1)
        i1.parent = None
        i1.delete()
        i2.parent = self
        self.instructions[idx] = i2

    def remove_instruction(self, i):
        """ Remove instruction from block """
        i.parent = None
        # i.delete()
        self.instructions.remove(i)
        return i

    @property
    def last_instruction(self):
        """ Gets the last instruction from the block """
        if not self.empty:
            return self.instructions[-1]

    @property
    def empty(self):
        """ Determines whether the block is empty or not """
        return len(self) == 0

    @property
    def first_instruction(self):
        return self.instructions[0]

    @property
    def phis(self):
        """ Return all phi instructions of this block """
        return [i for i in self.instructions if isinstance(i, Phi)]

    def get_successors(self):
        """ Get the direct successors of this block """
        successors = self.last_instruction.targets if not self.empty else []
        return successors + self.extra_successors

    successors = property(get_successors)

    def get_predecessors(self):
        b = set(i.block for i in self._preds)
        b |= set(self.extra_preds)

        # Make sure we have only active blocks:
        b &= set(self.parent.blocks)
        return list(b)

    predecessors = property(get_predecessors)

    def dominates(self, other):
        """ Check if this block dominates other block """
        assert self.function is not None
        assert self in self.function.blocks
        cfg_info = self.function.cfg_info
        return cfg_info.strictly_dominates(self, other)

    def change_target(self, old, new):
        """ Change the target of this block from old to new """
        self.last_instruction.change_target(old, new)

    def replace_incoming(self, block, new_blocks):
        """
            For each phi node in the block, change the incoming branch of
            block into new block with the same variable.
        """
        for phi in self.phis:
            value = phi.get_value(block)
            # First delete old incoming, to delete usage, do this now, not at
            # the end. If we do this at the end, we trash the newly added use.
            phi.del_incoming(block)

            # Add new incoming blocks:
            for b2 in new_blocks:
                phi.set_incoming(b2, value)


def var_use(name):
    """ Creates a property that also keeps track of usage """
    def getter(self):
        """ Gets the value """
        if name in self.var_map:
            return self.var_map[name]
        else:  # pragma: no cover
            raise KeyError(name)

    def setter(self, value):
        """ Sets the value """
        assert isinstance(value, Value)
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
    def __init__(self, loc=None):
        # Create a collection to store the values this value uses.
        # TODO: think of better naming..
        self.var_map = {}
        self.parent = None
        self.uses = set()
        self.loc = loc

    @property
    def block(self):
        """ The block in which this instruction is contained """
        return self.parent

    @property
    def function(self):
        """ Return the function this instruction is part of """
        return self.block.function

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
        """ replace value usage 'old' with new value, updating the def-use
            information.
        """
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

    @property
    def position(self):
        """ Return numerical position in block """
        return self.block.instructions.index(self)

    def dominates(self, other):
        """ Checks if this instruction dominates another instruction """
        if isinstance(self, (Parameter, Variable)):
            # TODO: hack, parameters and globals dominate all other
            # instructions..
            return True

        # All other instructions must have a containing block:
        assert self.block is not None, '{} has no block'.format(self)
        assert self in self.block.instructions

        # Phis are special case:
        if isinstance(other, Phi):
            for block in other.inputs:
                if other.inputs[block] == self:
                    # This is the queried dominance branch
                    # Check if this instruction dominates the last
                    # instruction of this block
                    return self.dominates(block.last_instruction)
            # pragma: no cover
            raise RuntimeError('Cannot query dominance for this phi')
        # For all other instructions follow these rules:
        if self.block == other.block:
            # fi = self.block.instructions.first_to_occur(self, other)
            return self.position < other.position
        else:
            return self.block.dominates(other.block)

    @property
    def IsTerminator(self):
        return isinstance(self, LastStatement)


class Value(Instruction):
    """ An instruction that results in a value has a type and a name """
    def __init__(self, name, ty, loc=None):
        super().__init__(loc=loc)
        assert isinstance(ty, Typ)
        assert isinstance(name, str)
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
        """ Determine whether this value is used anywhere """
        return bool(self.use_count)

    @property
    def use_count(self):
        """ Determine how often this values is used """
        return len(self.used_by)

    def replace_by(self, value):
        """ Replace all uses of this value by another value """
        for use in list(self.used_by):
            use.replace_use(self, value)


class Expression(Value):
    """ Base class for an expression """
    pass


class Cast(Expression):
    """ Base type conversion instruction """
    src = var_use('src')

    def __init__(self, value, name, ty):
        super().__init__(name, ty)
        assert isinstance(ty, Typ)
        self.src = value

    def __repr__(self):
        return '{} {} = cast {}'.format(self.ty, self.name, self.src.name)


def to_ptr(value, name):
    return Cast(value, name, ptr)


def to_i32(value, name):
    return Cast(value, name, i32)


def to_i8(value, name):
    return Cast(value, name, i8)


class Undefined(Value):
    def __repr__(self):
        return '{} = Undef'.format(self.name)


class Const(Expression):
    """ Represents a constant value """
    def __init__(self, value, name, ty):
        super().__init__(name, ty)
        self.value = value
        assert type(value) in [int, float], str(value)

    def __repr__(self):
        return '{} {} = {}'.format(self.ty, self.name, self.value)


class LiteralData(Expression):
    """ Instruction that contains labeled data. When generating code for this
        instruction, a label and its data is emitted in the literal area
    """
    def __init__(self, data, name):
        super().__init__(name, ptr)
        self.data = data
        assert type(data) in [bytes], str(data)

    def __repr__(self):
        return '{} = Literal {}'.format(self.name, hexlify(self.data))


class Call(Expression):
    """ Call a function with some arguments """
    def __init__(self, function_name, arguments, name, ty, loc=None):
        super().__init__(name, ty, loc=loc)
        assert isinstance(function_name, str)
        self.function_name = function_name
        self.arguments = arguments
        for arg in self.arguments:
            self.add_use(arg)

    def replace_use(self, old, new):
        idx = self.arguments.index(old)
        self.del_use(old)
        self.arguments[idx] = new
        self.add_use(new)

    def __repr__(self):
        args = ', '.join(arg.name for arg in self.arguments)
        return '{} = {}({})'.format(self.name, self.function_name, args)


# Data operations
class Binop(Expression):
    """ Generic binary operation """
    ops = ['+', '-', '*', '/', '%', '|', '&', '^', '<<', '>>']
    a = var_use('a')
    b = var_use('b')

    def __init__(self, a, operation, b, name, ty, loc=None):
        super().__init__(name, ty, loc=loc)
        assert operation in Binop.ops
        assert a.ty is b.ty
        self.a = a
        self.b = b
        self.operation = operation

    def __repr__(self):
        a, b, ty = self.a.name, self.b.name, self.ty
        return '{} {} = {} {} {}'.format(ty, self.name, a, self.operation, b)


class Unop(Expression):
    """ Unary operation """
    ops = ['-']
    a = var_use('a')

    def __init__(self, operation, a, name, ty):
        super().__init__(name, ty)
        assert operation in self.ops
        self.operation = operation
        assert a.ty is ty
        self.a = a


def Add(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '+', b, name, ty)


def Sub(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '-', b, name, ty)


def Mul(a, b, name, ty):
    """ Multiply a by b """
    return Binop(a, '*', b, name, ty)


class Phi(Value):
    """ Imaginary phi instruction to make SSA possible. """
    def __init__(self, name, ty):
        super().__init__(name, ty)
        self.inputs = {}

    def __repr__(self):
        inputs = {block.name: value.name
                  for block, value in self.inputs.items()}
        return '{} {} = Phi {}'.format(self.ty, self.name, inputs)

    def replace_use(self, old, new):
        """ Replace old value reference by new value reference """
        assert old in self.inputs.values()
        for inp in self.inputs:
            if self.inputs[inp] == old:
                self.del_use(old)
                self.inputs[inp] = new
                self.add_use(new)

    def set_incoming(self, block, value):
        """ Set the value for the phi node when entering through block """
        assert value.ty == self.ty
        if block in self.inputs:
            self.del_use(self.inputs[block])
        self.inputs[block] = value
        self.add_use(value)

    def get_value(self, block):
        """ Get the value for the incoming branch """
        return self.inputs[block]

    def del_incoming(self, block):
        """ Remove incoming branch from this phi node and delete the usage """
        value = self.inputs.pop(block)
        self.del_use(value)


class Alloc(Expression):
    """ Allocates space on the stack """
    def __init__(self, name, amount, loc=None):
        super().__init__(name, ptr, loc=loc)
        assert type(amount) is int
        self.amount = amount

    def __repr__(self):
        return '{} = Alloc {} bytes'.format(self.name, self.amount)


class Variable(Expression):
    """ Global variable, reserves room in the data area. Has name and size """
    def __init__(self, name, amount):
        super().__init__(name, ptr)
        assert isinstance(amount, int)
        self.amount = amount

    def __repr__(self):
        return 'Variable {} ({} bytes)'.format(self.name, self.amount)


class Parameter(Expression):
    """ Parameter of a function """
    def __init__(self, name, ty):
        super().__init__(name, ty)

    def __repr__(self):
        return 'Parameter {} {}'.format(self.ty, self.name)


class Load(Value):
    """ Load a value from memory """
    address = var_use('address')

    def __init__(self, address, name, ty, volatile=False):
        super().__init__(name, ty)
        assert address.ty is ptr
        self.address = address
        self.volatile = volatile

    def __repr__(self):
        return '{} {} = load {}'.format(self.ty, self.name, self.address.name)


class Store(Instruction):
    """ Store a value into memory """
    address = var_use('address')
    value = var_use('value')

    def __init__(self, value, address, volatile=False):
        super().__init__()
        assert address.ty is ptr
        self.address = address
        self.value = value
        self.volatile = volatile

    def __repr__(self):
        ty = self.value.ty
        val = self.value.name
        ptr = self.address.name
        return 'store {} {}, {}'.format(ty, val, ptr)


# Branching:
def block_ref(name):
    """ Creates a property that can be set and changed """
    def getter(self):
        if name in self.block_map:
            return self.block_map[name]
        else:  # pragma: no cover
            raise KeyError("No such block!")

    def setter(self, block):
        """ Sets the block reference """
        assert isinstance(block, Block)
        self.set_target_block(name, block)

    return property(getter, setter)


class LastStatement(Instruction):
    pass


class Terminator(LastStatement):
    """ Instruction that terminates the terminal block """
    def __init__(self):
        super().__init__()
        self.targets = []

    def __repr__(self):
        return 'Terminator'


class Return(LastStatement):
    """ Return statement. This instruction terminates a block and has as
        target the epilog block of a function.
    """
    result = var_use('result')

    def __init__(self, result):
        super().__init__()
        self.result = result

    def __repr__(self):
        return 'Return {}'.format(self.result.name)

    @property
    def targets(self):
        """ Gets a list of targets, in case of a return, this list only
            contains the epilog block!
        """
        return [self.function.epilog]


class JumpBase(LastStatement):
    """ Base of all jumping instructions """
    def __init__(self):
        super().__init__()
        self.block_map = {}

    def set_target_block(self, name, block):
        """ Set the target 'name' to block. Take into account that a block
            may already be pointed, so remove this reference!
        """
        # If block was present, remove this instruction from the block preds:
        if name in self.block_map:
            old_block = self.block_map[name]
            # check if old_block occurs only once in the block_map:
            if list(self.block_map.values()).count(old_block) == 1:
                old_block._preds.remove(self)

        # Use the new block:
        self.block_map[name] = block
        self.block_map[name]._preds.add(self)

    def delete(self):
        """ Clear references """
        while self.block_map:
            _, block = self.block_map.popitem()
            block._preds.remove(self)

    @property
    def targets(self):
        """ Gets a list of targets that this instruction jumps to """
        return list(self.block_map.values())

    def change_target(self, old, new):
        """ Change the target old into new """
        for name in self.block_map:
            if self.block_map[name] is old:
                self.set_target_block(name, new)


class Jump(JumpBase):
    """ Jump statement to another block within the same function """
    target = block_ref('target')

    def __init__(self, target):
        super().__init__()
        self.target = target

    def __repr__(self):
        return 'JUMP {}'.format(self.target.name)


class CJump(JumpBase):
    """ Conditional jump to true or false labels. """
    conditions = ['==', '<', '>', '>=', '<=', '!=']
    a = var_use('a')
    b = var_use('b')
    lab_yes = block_ref('lab_yes')
    lab_no = block_ref('lab_no')

    def __init__(self, a, cond, b, lab_yes, lab_no):
        super().__init__()
        assert cond in CJump.conditions
        self.a = a
        self.cond = cond
        self.b = b
        self.lab_yes = lab_yes
        self.lab_no = lab_no

    def __repr__(self):
        return 'IF {} {} {} THEN {} ELSE {}'\
               .format(self.a.name, self.cond, self.b.name,
                       self.lab_yes.name, self.lab_no.name)
