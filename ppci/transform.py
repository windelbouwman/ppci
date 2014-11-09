"""
 Transformation to optimize IR-code
"""

import logging
from . import ir


# Standard passes:

class ModulePass:
    """ Base class of all optimizing passes. Subclass this class
    to implement your own optimization pass
    """
    def __init__(self):
        self.logger = logging.getLogger(str(self.__class__.__name__))

    def prepare(self):
        pass


class FunctionPass(ModulePass):
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


class BlockPass(FunctionPass):
    def onFunction(self, f):
        for block in f.blocks:
            self.onBlock(block)

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
        instructions = list(block)
        count = 0
        for instruction in instructions:
            if type(instruction) is ir.Binop:
                if type(instruction.a) is ir.Const and \
                        (instruction.operation in self.ops) and \
                        type(instruction.b) is ir.Const:
                    # Now we can replace x = (4+5) with x = 9
                    a = instruction.a.value
                    b = instruction.b.value
                    v = self.ops[instruction.operation](a, b)
                    cn = ir.Const(v, 'new_fold', ir.i32)
                    block = instruction.block
                    block.insert_instruction(cn, before_instruction=instruction)
                    instruction.replace_by(cn)
                    count += 1

                if type(instruction.a) is ir.Binop and \
                        instruction.a.operation == '+' and \
                        type(instruction.a.b) is ir.Const and \
                        (instruction.operation == '+') and \
                        type(instruction.b) is ir.Const:
                    # Now we can replace x = (y+5)+5 with x = y + 10
                    a = instruction.a.b.value
                    b = instruction.b.value
                    cn = ir.Const(a + b, 'new_fold', ir.i32)
                    block = instruction.block
                    block.insert_instruction(cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    count += 1

                if type(instruction.a) is ir.Binop and \
                        instruction.a.operation == '-' and \
                        type(instruction.a.b) is ir.Const and \
                        instruction.operation == '-' and \
                        type(instruction.b) is ir.Const:
                    # Now we can replace x = (y-5)-5 with x = y - 10
                    a = instruction.a.b.value
                    b = instruction.b.value
                    cn = ir.Const(a + b, 'new_fold', ir.i32)
                    block = instruction.block
                    block.insert_instruction(cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    count += 1

        if count > 0:
            self.logger.debug('Folded {} expressions'.format(count))


class CommonSubexpressionEliminationPass(BlockPass):
    """ Replace common sub expressions with the previously defined one. """
    def onBlock(self, block):
        ins_map = {}
        stats = 0
        for i in block:
            if isinstance(i, ir.Binop):
                k = (i.a, i.operation, i.b)
            elif isinstance(i, ir.Const):
                k = (i.value,)
            else:
                continue
            if k in ins_map:
                ins_new = ins_map[k]
                i.replace_by(ins_new)
                stats += 1
            else:
                ins_map[k] = i
        if stats > 0:
            self.logger.debug('Replaced {} instructions'.format(stats))


class RemoveAddZeroPass(InstructionPass):
    """ Replace additions with zero with the value itself.
        Replace multiplication by 1 with value itself.
    """
    def onInstruction(self, instruction):
        if type(instruction) is ir.Binop:
            if instruction.operation == '+':
                if type(instruction.b) is ir.Const and instruction.b.value == 0:
                    instruction.replace_by(instruction.a)
                elif type(instruction.a) is ir.Const and instruction.a.value == 0:
                    instruction.replace_by(instruction.b)
            elif instruction.operation == '*':
                if type(instruction.b) is ir.Const and instruction.b.value == 1:
                    instruction.replace_by(instruction.a)


class DeleteUnusedInstructionsPass(BlockPass):
    """ Remove unused variables from a block """
    def onBlock(self, block):
        count = 0
        instructions = list(block.instructions)
        for instruction in instructions:
            if isinstance(instruction, ir.Value) and type(instruction) is not ir.Call:
                if not instruction.is_used:
                    instruction.remove_from_block()
                    count += 1
        if count > 0:
            self.logger.debug('Deleted {} unused instructions'.format(count))


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
    def find_store_backwards(self, i, stop_on=[ir.Call, ir.Store]):
        """ Go back from this instruction to beginning """
        block = i.block
        instructions = block.instructions
        pos = instructions.index(i)
        for x in range(pos - 1, 0, -1):
            i2 = instructions[x]
            if type(i2) is ir.Store:
                # Got first store!
                if i2.address is i.address:
                    return i2
                else:
                    return None
            elif type(i2) in stop_on:
                # A call can change memory, store not found..
                return None
        return None

    def onBlock(self, block):
        self.replace_load_after_store(block)
        self.remove_redundant_stores(block)

    def replace_load_after_store(self, block):
        """ Replace load after store with the value of the store """
        load_instructions = [ins for ins in block if isinstance(ins, ir.Load) and not ins.volatile]

        # Replace loads after store of same address by the stored value:
        count = 0
        for load in load_instructions:
            # Find store instruction preceeding this load:
            store = self.find_store_backwards(load)
            if store is not None:
                load.replace_by(store.value)
                count += 1
                # TODO: after one try, the instructions are different
                # reload of instructions required?
        if count > 0:
            self.logger.debug('Replaced {} loads after store'.format(count))

    def remove_redundant_stores(self, block):
        """ From two stores to the same address remove the previous one """
        store_instructions = [i for i in block if isinstance(i, ir.Store) and not i.volatile]

        count = 0
        # TODO: assume volatile memory stores always!
        # Replace stores to the same location:
        for store in store_instructions:
            store_prev = self.find_store_backwards(store, stop_on=[ir.Call, ir.Store, ir.Load])
            if store_prev is not None and not store_prev.volatile:
                store_prev.remove_from_block()

        if count > 0:
            self.logger.debug('Replaced {} redundant stores'.format(count))


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
