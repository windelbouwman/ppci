""" Transformation to optimize IR-code """

import logging
from .. import ir


class ModulePass:
    """ Base class of all optimizing passes.

    Subclass this class to implement your own optimization pass.
    """
    def __init__(self, debug_db=None):
        self.logger = logging.getLogger(str(self.__class__.__name__))
        self.debug_db = debug_db

    def __repr__(self):
        return self.__class__.__name__

    def prepare(self):
        pass

    def run(self, ir_module):  # pragma: no cover
        """ Run this pass over a module """
        raise NotImplementedError()


class FunctionPass(ModulePass):
    """ Base pass that loops over all functions in a module """
    def run(self, ir_module):
        """ Main entry point for the pass """
        self.prepare()
        assert isinstance(ir_module, ir.Module)
        for function in ir_module.functions:
            self.on_function(function)

    def on_function(self, f):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class BlockPass(FunctionPass):
    """ Base pass that loops over all blocks """
    def on_function(self, f):
        """ Loops over each block in the function """
        for block in f.blocks:
            self.on_block(block)

    def on_block(self, block):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class InstructionPass(BlockPass):
    """ Base pass that loops over all instructions """
    def on_block(self, block):
        """ Loops over each instruction in the block """
        for instruction in block:
            self.on_instruction(instruction)

    def on_instruction(self, ins):  # pragma: no cover
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


class LoadAfterStorePass(BlockPass):
    """ Remove load after store to the same location.

        .. code::

            [x] = a
            b = [x]
            c = b + 2

        transforms into:

        .. code::

            [x] = a
            c = a + 2
    """
    def find_store_backwards(
            self, i, ty,
            stop_on=[ir.FunctionCall, ir.ProcedureCall, ir.Store]):
        """ Go back from this instruction to beginning """
        block = i.block
        instructions = block.instructions
        pos = instructions.index(i)
        for x in range(pos - 1, 0, -1):
            i2 = instructions[x]
            if isinstance(i2, ir.Store) and ty is i2.value.ty:
                # Got first store!
                if i2.address is i.address:
                    return i2
                else:
                    return None
            elif type(i2) in stop_on:
                # A call can change memory, store not found..
                return None
        return None

    def on_block(self, block):
        self.replace_load_after_store(block)
        self.remove_redundant_stores(block)

    def replace_load_after_store(self, block):
        """ Replace load after store with the value of the store """
        load_instructions = [
            ins for ins in block if isinstance(ins, ir.Load) and
            not ins.volatile]

        # Replace loads after store of same address by the stored value:
        count = 0
        for load in load_instructions:
            # Find store instruction preceeding this load:
            store = self.find_store_backwards(load, load.ty)
            if store is not None:
                # Assert type equivalence:
                assert load.ty is store.value.ty
                load.replace_by(store.value)
                count += 1
                # TODO: after one try, the instructions are different
                # reload of instructions required?
        if count > 0:
            self.logger.debug('Replaced %s loads after store', count)

    def remove_redundant_stores(self, block):
        """ From two stores to the same address remove the previous one """
        store_instructions = [
            i for i in block if isinstance(i, ir.Store) and not i.volatile]

        count = 0
        # TODO: assume volatile memory stores always!
        # Replace stores to the same location:
        for store in store_instructions:
            store_prev = self.find_store_backwards(
                store, store.value.ty,
                stop_on=[ir.FunctionCall, ir.ProcedureCall, ir.Store, ir.Load])
            if store_prev is not None and not store_prev.volatile:
                store_prev.remove_from_block()

        if count > 0:
            self.logger.debug('Replaced %s redundant stores', count)
