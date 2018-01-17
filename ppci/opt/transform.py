""" Transformation to optimize IR-code """

import logging
import abc
from .. import ir


class ModulePass(metaclass=abc.ABCMeta):
    """ Base class of all optimizing passes.

    Subclass this class to implement your own optimization pass.
    """
    def __init__(self):
        self.logger = logging.getLogger(str(self.__class__.__name__))

    def __repr__(self):
        return self.__class__.__name__

    def prepare(self):
        pass

    @abc.abstractmethod
    def run(self, ir_module):  # pragma: no cover
        """ Run this pass over a module """
        raise NotImplementedError()


class FunctionPass(ModulePass):
    """ Base pass that loops over all functions in a module """
    def run(self, ir_module: ir.Module):
        """ Main entry point for the pass """
        self.prepare()
        self.debug_db = ir_module.debug_db
        assert isinstance(ir_module, ir.Module)
        for function in ir_module.functions:
            self.on_function(function)
        self.debug_db = None

    @abc.abstractmethod
    def on_function(self, function: ir.SubRoutine):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class BlockPass(FunctionPass):
    """ Base pass that loops over all blocks """
    def on_function(self, function):
        """ Loops over each block in the function """
        for block in function.blocks:
            self.on_block(block)

    @abc.abstractmethod
    def on_block(self, block: ir.Block):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class InstructionPass(BlockPass):
    """ Base pass that loops over all instructions """
    def on_block(self, block):
        """ Loops over each instruction in the block """
        for instruction in block:
            self.on_instruction(instruction)

    @abc.abstractmethod
    def on_instruction(self, instruction):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class RemoveAddZeroPass(InstructionPass):
    """ Replace additions with zero with the value itself.
        Replace multiplication by 1 with value itself.
    """
    def on_instruction(self, instruction):
        if type(instruction) is ir.Binop:
            if instruction.operation == '+':
                if type(instruction.b) is ir.Const \
                        and instruction.b.value == 0:
                    instruction.replace_by(instruction.a)
                elif type(instruction.a) is ir.Const \
                        and instruction.a.value == 0:
                    instruction.replace_by(instruction.b)
            elif instruction.operation == '*':
                if type(instruction.b) is ir.Const \
                        and instruction.b.value == 1:
                    instruction.replace_by(instruction.a)


class DeleteUnusedInstructionsPass(BlockPass):
    """ Remove unused variables from a block """
    def on_block(self, block):
        unused_instructions = [
            i for i in block
            if (isinstance(i, ir.Value) and
                (not isinstance(i, ir.FunctionCall)) and
                (not i.is_used))]
        count = len(unused_instructions)
        for instruction in unused_instructions:
            instruction.remove_from_block()
        if count > 0:
            self.logger.debug('Deleted %i unused instructions', count)
