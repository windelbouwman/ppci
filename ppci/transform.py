"""
 Transformation to optimize IR-code
"""

import logging
from . import ir


# Standard passes:

class FunctionPass:
    def __init__(self):
        self.logger = logging.getLogger(str(self.__class__.__name__))

    def run(self, ir_module):
        """ Main entry point for the pass """
        self.logger.debug('Running pass {}'.format(self.__class__.__name__))
        self.prepare()
        if isinstance(ir_module, ir.Module):
            for f in ir_module.Functions:
                self.onFunction(f)
        elif isinstance(ir_module, ir.Function):
            self.onFunction(ir_module)
        else:
            raise Exception()

    def onFunction(self, f):
        """ Override this virtual method """
        raise NotImplementedError()

    def prepare(self):
        pass


class BlockPass(FunctionPass):
    def onFunction(self, f):
        for bb in f.Blocks:
            self.onBlock(bb)

    def onBlock(self, bb):
        """ Override this virtual method """
        raise NotImplementedError()


class InstructionPass(BlockPass):
    def onBlock(self, bb):
        for ins in iter(bb.Instructions):
            self.onInstruction(ins)

    def onInstruction(self, ins):
        """ Override this virtual method """
        raise NotImplementedError()


# Usefull transforms:
class ConstantFolder(BlockPass):
    """ Try to fold common constant expressions """
    def __init__(self):
        super().__init__()
        self.ops = {}
        self.ops['+'] = lambda x, y: x + y
        self.ops['-'] = lambda x, y: x - y
        self.ops['*'] = lambda x, y: x * y
        self.ops['<<'] = lambda x, y: x << y

    def onBlock(self, block):
        pass
        for instruction in block.instructions:
            if type(instruction) is ir.Binop:
                if type(instruction.b) is ir.Binop and type(instruction.b.b) is ir.Const:
                    # TODO
                    pass

    def postExpr(self, expr):
        if type(i) is BinaryOperator and i.operation in self.ops.keys() and type(i.a) is Const and type(i.b) is Const:
            vr = self.ops[i.operation](i.a.value, i.b.value)
            return Const(vr)
        else:
            return expr


class DeadCodeDeleter(BlockPass):
    def onBlock(self, bb):
        def instructionUsed(ins):
            if not type(ins) in [ImmLoad, BinaryOperator]:
                return True
            if len(ins.defs) == 0:
                # In case this instruction does not define any 
                # variables, assume it is usefull.
                return True
            return any(d.Used for d in ins.defs)

        change = True
        while change:
            change = False
            for i in bb.Instructions:
                if instructionUsed(i):
                    continue
                bb.removeInstruction(i)
                change = True


class CommonSubexpressionEliminationPass(FunctionPass):
    """ Replace common sub expressions with the previously defined one """
    def onFunction(self, function):
        for block in function.Blocks:
            ins_map = {}
            for i in block.Instructions:
                if isinstance(i, ir.Binop):
                    k = (i.a, i.operation, i.b)
                    if k in ins_map:
                        ins_new = ins_map[k]
                        logging.debug('Replacing {} with {}'.format(i, ins_new))
                        i.replace_by(ins_new)
                    else:
                        ins_map[k] = i


class RemoveAddZeroPass(InstructionPass):
    """ Replace additions with zero with the value itself """
    def onInstruction(self, instruction):
        if type(instruction) is ir.Binop:
            if instruction.operation == '+':
                if type(instruction.b) is ir.Const and instruction.b.value == 0:
                    self.logger.debug('Folding {} to {}'.format(instruction, instruction.a))
                    instruction.replace_by(instruction.a)
            elif instruction.operation == '*':
                if type(instruction.b) is ir.Const and instruction.b.value == 1:
                    self.logger.debug('Multiple 1 {} to {}'.format(instruction, instruction.a))
                    raise NotImplementedError()


class DeleteUnusedInstructionsPass(BlockPass):
    """ Remove unused variables from a block """
    def onBlock(self, block):
        instructions = list(block.instructions)
        for instruction in instructions:
            if isinstance(instruction, ir.Value) and type(instruction) is not ir.Call:
                if not instruction.is_used:
                    self.logger.debug('Deleting unused: {}'.format(instruction))
                    instruction.remove_from_block()


class CleanPass(FunctionPass):
    """ Glue blocks together if possible """
    def onFunction(self, f):
        self.remove_empty_blocks(f)
        self.remove_one_preds(f)

    def remove_empty_blocks(self, f):
        """ Remove empty basic blocks from function. """
        # If a block only contains a branch, it can be removed:
        empty = lambda b: type(b.FirstInstruction) is ir.Jump
        empty_blocks = list(filter(empty, f.Blocks))
        for b in empty_blocks:
            # Update predecessors
            preds = b.Predecessors
            if b not in preds + [f.entry]:
                # Do not remove if preceeded by itself
                tgt = b.LastInstruction.target
                for pred in preds:
                      pred.LastInstruction.changeTarget(b, tgt)
                self.logger.debug('Removing empty block: {}'.format(b))
                f.removeBlock(b)

    def remove_one_preds(self, f):
        """ Remove basic blocks with only one predecessor """
        change = True
        while change:
            change = False
            for block in f.Blocks:
                preds = block.Predecessors
                if len(preds) == 1 and block not in preds and type(preds[0].LastInstruction) is ir.Jump and block is not f.epiloog:
                    self.glue_blocks(preds[0], block, f)
                    change = True

    def glue_blocks(self, block1, block2, f):
        """ Glue two blocks together into the first block """
        self.logger.debug('Merging {} and {}'.format(block1.name, block2.name))

        # Remove the last jump:
        block1.removeInstruction(block1.LastInstruction)

        # Copy all instructions to block1:
        for instruction in block2.Instructions:
            block1.addInstruction(instruction)
        # This does not work somehow:
        #block2.parent.removeBlock(block2)
