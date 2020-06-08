""" Constructing IR.

"""

import contextlib
from .. import ir
from ..binutils.debuginfo import DebugLocation


def split_block(block, pos=None, newname="splitblock"):
    """ Split a basic block into two which are connected.

    Note to take care of phi instructions of successors
    and make sure to update those phi instructions.
    """

    downstream_phis = []
    for successor_block in block.successors:
        for phi in successor_block.phis:
            downstream_phis.append(phi)

    if pos is None:
        pos = int(len(block) / 2)
    rest = block.instructions[pos:]
    assert all(not i.is_phi for i in rest)

    # Create new block, and move instructions into it:
    block2 = ir.Block(newname)
    block.function.add_block(block2)
    for instruction in rest:
        block.remove_instruction(instruction)
        block2.add_instruction(instruction)

    # Update successor phi nodes:
    for phi in downstream_phis:
        value = phi.get_value(block)
        phi.del_incoming(block)
        phi.set_incoming(block2, value)

    # Add a jump to the original block:
    block.add_instruction(ir.Jump(block2))
    return block, block2


class Builder:
    """ Helper class for IR-code generators.

    This class can assist in the generation of IR-code.
    It's purpose is to simplify the language frontend,
    as well as to hide a bit of IR classes from the
    frontends.
    """

    def __init__(self):
        self.block = None
        self.module = None
        self.function = None
        self.block_number = 0
        self.prepare()
        self.location = None
        self._location_stack = []

    def prepare(self):
        self.block = None
        self.module = None
        self.function = None

    # Helpers:
    def set_module(self, module):
        self.module = module

    def new_function(self, name, binding, return_ty):
        """ Create a new function. """
        assert self.module is not None
        function = ir.Function(name, binding, return_ty)
        self.module.add_function(function)
        return function

    def new_procedure(self, name, binding):
        """ Create a new procedure. """
        assert self.module is not None
        procedure = ir.Procedure(name, binding)
        self.module.add_function(procedure)
        return procedure

    def new_block(self, name=None):
        """ Create a new block and add it to the current function """
        assert self.function is not None
        if name is None:
            name = "{}_block{}".format(self.function.name, self.block_number)
            self.block_number += 1
        block = ir.Block(name)
        self.function.add_block(block)
        return block

    def set_function(self, function):
        self.function = function
        self.block = function.entry if function else None
        self.block_number = 0

    def set_block(self, block):
        self.block = block

    def emit(self, instruction: ir.Instruction) -> ir.Instruction:
        """ Append an instruction to the current block """
        assert isinstance(instruction, ir.Instruction), str(instruction)
        assert self.block is not None
        self.block.add_instruction(instruction)

        if self.location and self.module.debug_db:
            # Associate debug info:
            self.module.debug_db.enter(
                instruction, DebugLocation(self.location)
            )

        return instruction

    # Instruction helpers:
    def emit_jump(self, block):
        """ Emit a jump instruction to the given block. """
        self.emit(ir.Jump(block))

    def emit_return(self, value):
        """ Emit a return instruction. """
        self.emit(ir.Return(value))

    def emit_exit(self):
        """ Emit exit instruction. """
        self.emit(ir.Exit())

    def emit_load(self, address, ty, volatile=False):
        """ Emit a load instruction. """
        # TBD: rename all temporaries to tmp001 etc...
        return self.emit(ir.Load(address, "tmp_load", ty, volatile=volatile))

    def emit_binop(self, a, op, b, ty):
        """ Emit a binary operation.

        Args:
            a: operand 1
            op: the operation to perform.
            b: operand 2, can be either a value or an int.
            ty: The type of a, b and the result.
        
        Returns:
            The result value of the binary operation.
        """

        # Auto-inject constant instruction.
        if isinstance(b, int):
            b = self.emit_const(b, ty)
        return self.emit(ir.Binop(a, op, b, "tmp", ty))

    def emit_add(self, a, b, ty):
        """ Emit addition operation. """
        return self.emit_binop(a, "+", b, ty)

    def emit_mul(self, a, b, ty):
        """ Emit multiplication operation. """
        return self.emit_binop(a, "*", b, ty)

    def emit_sub(self, a, b, ty):
        """ Emit subtract operation. """
        return self.emit_binop(a, "-", b, ty)

    def emit_const(self, value, ty):
        """ Emit a constant. """
        return self.emit(ir.Const(value, "num", ty))

    def emit_cast(self, value, ty):
        """ Emit a type cast instruction. """
        return self.emit(ir.Cast(value, "typecast", ty))

    # Debug helpers:
    def set_location(self, location):
        """ Set the current source code location.

        All instructions emitted from now on will be associated
        with the given sourcecode.
        """
        self.location = location

    def push_location(self, location):
        self._location_stack.append(location)
        self.set_location(location)

    def pop_location(self):
        self._location_stack.pop()
        if self._location_stack:
            self.location = self._location_stack[-1]
        else:
            self.location = None

    @contextlib.contextmanager
    def use_location(self, location):
        """ Use the location for all code generated
        within a context.
        """
        self.push_location(location)
        yield
        self.pop_location()
