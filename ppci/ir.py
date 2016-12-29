"""
Intermediate representation (IR) code classes. Ir-code is organized into
modules. Modules may contain functions and global variables. Functions
consist of basic blocks. Each basic block is a linear sequence of instructions.

The only types available are basic integer types and a pointer type.
"""

# pylint: disable=R0903

from binascii import hexlify
import logging


class Module:
    """ Container unit for variables and functions. """
    def __init__(self, name):
        self.name = name
        self._functions = []
        self._variables = []

    def __str__(self):
        return 'module {0}'.format(self.name)

    def add_function(self, function):
        """ Add a function to this module """
        assert isinstance(function, SubRoutine)
        self._functions.append(function)
        function.module = self

    def add_variable(self, variable):
        """ Add a variable to this module """
        assert isinstance(variable, Variable)
        self._variables.append(variable)
        variable.module = self

    @property
    def variables(self):
        """ Get all variables of this module """
        return self._variables

    @property
    def functions(self):
        """ Get all functions of this module """
        return self._functions

    def stats(self):
        """ Returns a string with statistic information such as block count """
        num_functions = len(self.functions)
        num_blocks = sum(len(f.blocks) for f in self.functions)
        num_instructions = sum(f.num_instructions() for f in self.functions)
        return "functions: {}, blocks: {}, instructions: {}" \
            .format(num_functions,
                    num_blocks,
                    num_instructions)


class SubRoutine:
    """ Base class of function and procedure. These two differ in that
    a function returns a value, where as a procedure does not.

    Design trade-off:
    In C, a void type is introduced to permit functions that return nothing
    (void). This seems somewhat artificial, but keeps things simple for the
    users. In pascal, the procedure and function types are explicit, and the
    void type is not needed. This is also the approach taken here.

    So instead of a Function and Call types, we have Function, Procedure,
    FunctionCall and ProcedureCall types.
    """

    logger = logging.getLogger('irfunc')

    def __init__(self, name):
        self.name = name
        self.blocks = []
        self.entry = None
        self.defined_names = set()
        self.unique_counter = 0
        self.arguments = []

    def make_unique_name(self, dut):
        """ Check if the name of the given dut is unique
            and if not make it so.
            Also add it to the used names """
        name = dut.name
        while dut.name in self.defined_names:
            dut.name = '{}_{}'.format(name, self.unique_counter)
            self.unique_counter += 1
        self.defined_names.add(dut.name)

    def dump(self):
        """ Print this function """
        print(self)
        for block in self:
            block.dump()

    def __iter__(self):
        """ Iterate over all blocks in this function """
        for block in self.blocks:
            yield block

    @property
    def block_names(self):
        """ Get the names of all the blocks in this function """
        return (b.name for b in self.blocks)

    def calc_reachable_blocks(self):
        """ Determine all blocks that can be reached """
        blocks = {self.entry}
        worklist = [self.entry]
        while worklist:
            block = worklist.pop()
            for successor in block.successors:
                if successor not in blocks:
                    blocks.add(successor)
                    worklist.append(successor)
        return blocks

    def delete_unreachable(self):
        """ Calculate all reachable blocks from entry and delete all others """
        reachable = self.calc_reachable_blocks()
        unreachable = {b for b in self if b not in reachable}
        for block in unreachable:
            il = list(block)
            for instruction in il:
                block.remove_instruction(instruction)
                self.logger.debug('deleting %s', instruction)
                instruction.delete()
        for block in unreachable:
            self.logger.debug('deleting block %s', block.name)
            self.remove_block(block)
            block.delete()

    def add_block(self, block):
        """ Add a block to this function """
        assert block.name not in self.block_names
        block.function = self
        self.make_unique_name(block)
        self.blocks.append(block)
        return block

    def remove_block(self, block):
        """ Remove a block from this function """
        block.function = None
        self.blocks.remove(block)

    def add_parameter(self, parameter):
        """ Add an argument to this function """
        assert isinstance(parameter, Parameter)
        parameter.num = len(self.arguments)
        self.arguments.append(parameter)
        # p.parent = self.entry

    def num_instructions(self):
        """ Count the number of instructions contained in this function """
        return sum(len(block) for block in self.blocks)


class Procedure(SubRoutine):
    """ A procedure definition that does not return a value """
    def __str__(self):
        args = ', '.join('{} {}'.format(a.ty, a.name) for a in self.arguments)
        return 'procedure {}({})'.format(self.name, args)


class Function(SubRoutine):
    """ Represents a function. """

    def __init__(self, name, return_ty):
        super().__init__(name)
        assert isinstance(return_ty, Typ)
        self.return_ty = return_ty

    def __str__(self):
        args = ', '.join('{} {}'.format(a.ty, a.name) for a in self.arguments)
        ret_typ = self.return_ty
        return 'function {} {}({})'.format(ret_typ, self.name, args)


class Block:
    """ Uninterrupted sequence of instructions.

    A block is properly terminated if its last instruction is a
    :class:`FinalInstruction`.
    """
    def __init__(self, name):
        self.name = name
        self.function = None
        self.instructions = list()
        self.references = set()

    def dump(self):
        print('  ', self)
        for instruction in self:
            print('    ', instruction)

    def __str__(self):
        return '{0}:'.format(self.name)

    def __iter__(self):
        for instruction in self.instructions:
            yield instruction

    def __len__(self):
        return len(self.instructions)

    def insert_instruction(self, instruction, before_instruction=None):
        """ Insert an instruction at the front of the block """
        if before_instruction is not None:
            assert self == before_instruction.block
            pos = before_instruction.position
        else:
            pos = 0
        instruction.block = self
        self.instructions.insert(pos, instruction)
        if isinstance(instruction, Value):
            self.function.make_unique_name(instruction)

    def add_instruction(self, instruction):
        """ Add an instruction to the end of this block """
        assert not self.is_closed
        instruction.block = self
        self.instructions.append(instruction)
        if isinstance(instruction, Value):
            self.function.make_unique_name(instruction)

    def remove_instruction(self, instruction):
        """ Remove instruction from block """
        instruction.block = None
        self.instructions.remove(instruction)
        return instruction

    @property
    def last_instruction(self):
        """ Gets the last instruction from the block """
        if not self.is_empty:
            return self.instructions[-1]

    @property
    def is_empty(self):
        """ Determines whether the block is empty or not """
        return len(self) == 0

    @property
    def is_closed(self):
        """ Determine whether this block is propert terminated """
        return isinstance(self.last_instruction, FinalInstruction)

    @property
    def is_entry(self):
        """ Check if this block is the entry block of a function """
        return self.function.entry is self

    @property
    def first_instruction(self):
        """ Return this blocks first instruction """
        return self.instructions[0]

    @property
    def phis(self):
        """ Return all phi instructions of this block """
        return [i for i in self.instructions if isinstance(i, Phi)]

    @property
    def successors(self):
        """ Get the direct successors of this block """
        return self.last_instruction.targets

    @property
    def predecessors(self):
        """ Return all predecessing blocks """
        return [i.block for i in self.references]

    @property
    def is_used(self):
        """ True if this block is referenced by an instruction """
        return len(self.references) > 0

    def change_target(self, old, new):
        """ Change the target of this block from old to new """
        self.last_instruction.change_target(old, new)

    def delete(self):
        """ Delete all instructions in this block, so it can be removed """
        assert not self.is_used
        for instruction in self:
            instruction.delete()

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


def value_use(name):
    """ Creates a property that also keeps track of usage """
    def getter(self):
        """ Gets the value """
        if name in self._var_map:
            return self._var_map[name]
        else:  # pragma: no cover
            raise KeyError(name)

    def setter(self, value):
        """ Sets the value """
        assert isinstance(value, Value)
        # If value was already set, remove usage
        if name in self._var_map:
            self.del_use(self._var_map[name])

        # Place the value in the var map:
        self._var_map[name] = value

        # Add usage:
        self.add_use(value)

    return property(getter, setter)


class Instruction:
    """ Base class for all instructions that go into a basic block """
    def __init__(self):
        # Create a collection to store the values this value uses.
        # TODO: think of better naming..
        self._var_map = {}
        self.block = None
        self.uses = set()

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

    def delete(self):
        assert not self.uses

    def replace_use(self, old, new):
        """ replace value usage 'old' with new value, updating the def-use
            information.
        """
        # TODO: update reference
        assert old in self._var_map.values()
        for name in self._var_map:
            if self._var_map[name] is old:
                self.del_use(old)
                self._var_map[name] = new
                self.add_use(new)

    def remove_from_block(self):
        for use in list(self.uses):
            self.del_use(use)
        self.block.remove_instruction(self)

    @property
    def position(self):
        """ Return numerical position in block """
        return self.block.instructions.index(self)

    @property
    def is_terminator(self):
        """ Check if this instruction is a block terminating instruction """
        return isinstance(self, FinalInstruction)


class Typ:
    """ Built in type representation """
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @property
    def is_integer(self):
        """ Test if this type is of integer type """
        return isinstance(self, IntegerTyp)


class IntegerTyp(Typ):
    """ Integer type """
    def __init__(self, name, bits):
        super().__init__(name)
        self.bits = bits


class SignedIntegerTyp(IntegerTyp):
    """ Signed integer type """
    signed = True


class UnsignedIntegerTyp(IntegerTyp):
    """ Unsigned integer type """
    signed = False


# The builtin types:
f64 = Typ('f64')  #: 64-bit floating point type
f32 = Typ('f32')  #: 32-bit floating point type
i64 = SignedIntegerTyp('i64', 64)  #: Signed 64-bit type
i32 = SignedIntegerTyp('i32', 32)  #: Signed 32-bit type
i16 = SignedIntegerTyp('i16', 16)  #: Signed 16-bit type
i8 = SignedIntegerTyp('i8', 8)  #: Signed 8-bit type
u64 = UnsignedIntegerTyp('u64', 64)  #: Unsigned 64-bit type
u32 = UnsignedIntegerTyp('u32', 32)  #: Unsigned 32-bit type
u16 = UnsignedIntegerTyp('u16', 16)  #: Unsigned 16-bit type
u8 = UnsignedIntegerTyp('u8', 8)  #: Unsigned 8-bit type
ptr = Typ('ptr')  #: Pointer type

value_types = [f64, f32, i64, i32, i16, i8, u64, u32, u16, u8]
all_types = value_types + [ptr]


class Value(Instruction):
    """ An instruction that results in a value has a type and a name """
    def __init__(self, name, ty):
        super().__init__()
        assert isinstance(ty, Typ)
        assert isinstance(name, str)
        self.name = name
        self.ty = ty
        self.used_by = set()

    def __add__(self, other):
        """ Add this value to another one """
        assert isinstance(other, Value)
        assert self.ty is other.ty
        return Binop(self, '+', other, 'add', self.ty)

    def __sub__(self, other):
        """ Substract other value from this one """
        assert isinstance(other, Value)
        assert self.ty is other.ty
        return Binop(self, '-', other, 'sub', self.ty)

    def __mul__(self, other):
        """ Multiply this value with another one """
        assert isinstance(other, Value)
        assert self.ty is other.ty
        return Binop(self, '*', other, 'mul', self.ty)

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


class Cast(Value):
    """ Base type conversion instruction """
    src = value_use('src')

    def __init__(self, value, name, ty):
        super().__init__(name, ty)
        self.src = value

    def __str__(self):
        return '{} {} = cast {}'.format(self.ty, self.name, self.src.name)


class Undefined(Value):
    """ Undefined value, this value must never be used. """
    def __str__(self):
        return '{} = undefined'.format(self.name)


class Const(Value):
    """ Represents a constant value """
    def __init__(self, value, name, ty):
        super().__init__(name, ty)
        self.value = value
        assert isinstance(value, (int, float)), str(value)

    def __str__(self):
        return '{} {} = {}'.format(self.ty, self.name, self.value)


class LiteralData(Value):
    """ Instruction that contains labeled data. When generating code for this
        instruction, a label and its data is emitted in the literal area
    """
    def __init__(self, data, name):
        super().__init__(name, ptr)
        self.data = data
        assert isinstance(data, bytes), str(data)

    def __str__(self):
        data = hexlify(self.data)
        return '{} {} = Literal {}'.format(self.ty, self.name, data)


class FunctionCall(Value):
    """ Call a function with some arguments and a return value """
    def __init__(self, function_name, arguments, name, ty):
        super().__init__(name, ty)
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

    def __str__(self):
        args = ', '.join(arg.name for arg in self.arguments)
        return '{} {} = {}({})'.format(
            self.ty, self.name, self.function_name, args)


class ProcedureCall(Instruction):
    """ Call a procedure with some arguments """
    def __init__(self, function_name, arguments):
        super().__init__()
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

    def __str__(self):
        args = ', '.join(arg.name for arg in self.arguments)
        return '{}({})'.format(self.function_name, args)


class Binop(Value):
    """ Generic binary operation """
    ops = ['+', '-', '*', '/', '%', '|', '&', '^', '<<', '>>']
    a = value_use('a')
    b = value_use('b')

    def __init__(self, a, operation, b, name, ty):
        super().__init__(name, ty)
        assert operation in Binop.ops
        assert a.ty is b.ty is ty
        self.a = a
        self.b = b
        self.operation = operation

    def __str__(self):
        a, b, ty = self.a.name, self.b.name, self.ty
        return '{} {} = {} {} {}'.format(ty, self.name, a, self.operation, b)


def add(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '+', b, name, ty)


def sub(a, b, name, ty):
    """ Substract b from a """
    return Binop(a, '-', b, name, ty)


def mul(a, b, name, ty):
    """ Multiply a by b """
    return Binop(a, '*', b, name, ty)


class Phi(Value):
    """ Imaginary phi instruction to make SSA possible. """
    def __init__(self, name, ty):
        super().__init__(name, ty)
        self.inputs = {}

    def __str__(self):
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


class Alloc(Value):
    """ Allocates space on the stack. The type of this value is a ptr """
    def __init__(self, name, amount):
        super().__init__(name, ptr)
        assert isinstance(amount, int)
        self.amount = amount

    def __str__(self):
        return '{} {} = alloc {} bytes'.format(self.ty, self.name, self.amount)


# TODO: Variable now inherits Value and hence Instruction, but it is not an
# instruction!
class Variable(Value):
    """ Global variable, reserves room in the data area. Has name and size """
    def __init__(self, name, amount, value=None):
        super().__init__(name, ptr)
        assert isinstance(amount, int)
        self.amount = amount
        assert value is None or isinstance(value, bytes)
        if isinstance(value, bytes):
            assert len(value) == amount
        self.value = value

    def __str__(self):
        return 'variable {} ({} bytes)'.format(self.name, self.amount)


class Parameter(Value):
    """ Parameter of a function """
    def __init__(self, name, ty):
        super().__init__(name, ty)

    def __str__(self):
        return 'Parameter {} {}'.format(self.ty, self.name)


class Load(Value):
    """ Load a value from memory """
    address = value_use('address')

    def __init__(self, address, name, ty, volatile=False):
        super().__init__(name, ty)
        assert address.ty is ptr
        self.address = address
        self.volatile = volatile

    def __str__(self):
        return '{} {} = load {}'.format(self.ty, self.name, self.address.name)


class Store(Instruction):
    """ Store a value into memory """
    address = value_use('address')
    value = value_use('value')

    def __init__(self, value, address, volatile=False):
        super().__init__()
        assert address.ty is ptr
        self.address = address
        self.value = value
        self.volatile = volatile

    def __str__(self):
        val = self.value.name
        address = self.address.name
        return 'store {}, {}'.format(val, address)


class FinalInstruction(Instruction):
    """ Final instruction in a basic block """
    pass


class Exit(FinalInstruction):
    """ Instruction that exits the procedure. """
    def __init__(self):
        super().__init__()
        self.targets = []

    def __str__(self):
        return 'exit'


class Return(FinalInstruction):
    """ This instruction returns a value and exits the function. """
    result = value_use('result')

    def __init__(self, result):
        super().__init__()
        self.result = result
        self.targets = []

    def __str__(self):
        return 'return {}'.format(self.result.name)


def block_use(name):
    """ Creates a property that can be set and changed """
    def getter(self):
        """ Gets the block reference """
        if name in self._block_map:
            return self._block_map[name]
        else:  # pragma: no cover
            raise KeyError("No such block!")

    def setter(self, block):
        """ Sets the block reference """
        assert isinstance(block, Block)
        self.set_target_block(name, block)

    return property(getter, setter)


class JumpBase(FinalInstruction):
    """ Base of all jumping instructions """
    def __init__(self):
        super().__init__()
        self._block_map = {}

    def set_target_block(self, name, block):
        """ Set the target 'name' to block. Take into account that a block
            may already be pointed, so remove this reference!
        """
        # If block was present, remove this instruction from the block preds:
        if name in self._block_map:
            old_block = self._block_map[name]
            # check if old_block occurs only once in the block_map:
            if list(self._block_map.values()).count(old_block) == 1:
                old_block.references.remove(self)

        # Use the new block:
        self._block_map[name] = block
        self._block_map[name].references.add(self)

    def delete(self):
        """ Clear references """
        while self._block_map:
            _, block = self._block_map.popitem()
            block.references.remove(self)

    @property
    def targets(self):
        """ Gets a list of targets that this instruction jumps to """
        return list(self._block_map.values())

    def change_target(self, old, new):
        """ Change the target old into new """
        for name in self._block_map:
            if self._block_map[name] is old:
                self.set_target_block(name, new)


class Jump(JumpBase):
    """ Jump statement to another block within the same function """
    target = block_use('target')

    def __init__(self, target):
        super().__init__()
        self.target = target

    def __str__(self):
        return 'jmp {}'.format(self.target.name)


class CJump(JumpBase):
    """ Conditional jump to true or false labels. """
    conditions = ['==', '<', '>', '>=', '<=', '!=']
    a = value_use('a')
    b = value_use('b')
    lab_yes = block_use('lab_yes')
    lab_no = block_use('lab_no')

    def __init__(self, a, cond, b, lab_yes, lab_no):
        super().__init__()
        assert cond in CJump.conditions
        self.a = a
        self.cond = cond
        self.b = b
        self.lab_yes = lab_yes
        self.lab_no = lab_no

    def __str__(self):
        return 'cjmp {} {} {} ? {} : {}'\
               .format(self.a.name, self.cond, self.b.name,
                       self.lab_yes.name, self.lab_no.name)
