""" Constructing IR.

"""

from .. import ir


def split_block(block, pos=None, newname="splitblock"):
    """ Split a basic block into two which are connected """
    if pos is None:
        pos = int(len(block) / 2)
    rest = block.instructions[pos:]
    block2 = ir.Block(newname)
    block.function.add_block(block2)
    for instruction in rest:
        block.remove_instruction(instruction)
        block2.add_instruction(instruction)

    # Add a jump to the original block:
    block.add_instruction(ir.Jump(block2))
    return block, block2


class Builder:
    """ Base class for ir code generators """

    def __init__(self):
        self.block = None
        self.module = None
        self.function = None
        self.block_number = 0
        self.prepare()

    def prepare(self):
        self.block = None
        self.module = None
        self.function = None

    # Helpers:
    def set_module(self, module):
        self.module = module

    def new_function(self, name, binding, return_ty):
        assert self.module is not None
        function = ir.Function(name, binding, return_ty)
        self.module.add_function(function)
        return function

    def new_procedure(self, name, binding):
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

    def emit_load(self, address, ty):
        """ Emit a load instruction. """
        # TBD: rename all temporaries to tmp001 etc...
        return self.emit(ir.Load(address, "tmp_load", ty))

    def emit_binop(self, a, op, b, ty):
        """ Emit a binary operation. """
        return self.emit(ir.Binop(a, op, b, "add", ty))

    def emit_const(self, value, ty):
        """ Emit a constant. """
        return self.emit(ir.Const(value, "num", ty))
