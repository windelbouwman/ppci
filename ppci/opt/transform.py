"""
 Transformation to optimize IR-code
"""

import logging
from .. import ir


# Standard passes:

class ModulePass:
    """ Base class of all optimizing passes. Subclass this class
    to implement your own optimization pass
    """
    def __init__(self, debug_db):
        self.logger = logging.getLogger(str(self.__class__.__name__))
        self.debug_db = debug_db

    def __repr__(self):
        return self.__class__.__name__

    def prepare(self):
        pass


class FunctionPass(ModulePass):
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
    def on_function(self, f):
        for block in f.blocks:
            self.on_block(block)

    def on_block(self, block):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


class InstructionPass(BlockPass):
    def on_block(self, block):
        for instruction in block:
            self.on_instruction(instruction)

    def on_instruction(self, ins):  # pragma: no cover
        """ Override this virtual method """
        raise NotImplementedError()


# Usefull transforms:
class ConstantFolder(BlockPass):
    """ Try to fold common constant expressions """
    def __init__(self, debug_db):
        super().__init__(debug_db)
        self.ops = {}
        self.ops['+'] = lambda x, y: x + y
        self.ops['-'] = lambda x, y: x - y
        self.ops['*'] = lambda x, y: x * y
        self.ops['<<'] = lambda x, y: x << y

    def is_const(self, value):
        """ Determine if a value can be evaluated as a constant value """
        if type(value) is ir.Const:
            return True
        elif isinstance(value, ir.Cast):
            return self.is_const(value.src)
        elif isinstance(value, ir.Binop):
            return value.operation in self.ops and \
                self.is_const(value.a) and self.is_const(value.b)
        else:
            return False

    def eval_const(self, value):
        """ Evaluate expression, and return a new const instance """
        if type(value) is ir.Const:
            return value
        elif type(value) is ir.Binop:
            a = self.eval_const(value.a)
            b = self.eval_const(value.b)
            assert a.ty is b.ty
            assert a.ty is value.ty
            v = self.ops[value.operation](a.value, b.value)
            cn = ir.Const(v, 'new_fold', a.ty)
            return cn
        elif type(value) is ir.Cast:
            c_val = self.eval_const(value.src)
            return ir.Const(c_val.value, "casted", value.ty)
        else:  # pragma: no cover
            raise NotImplementedError(str(value))

    def on_block(self, block):
        instructions = list(block)
        count = 0
        for instruction in instructions:
            if not isinstance(instruction, ir.Const) and \
                    self.is_const(instruction):
                # Now we can replace x = (4+5) with x = 9
                cnst = self.eval_const(instruction)
                block.insert_instruction(cnst, before_instruction=instruction)
                instruction.replace_by(cnst)
                count += 1
            else:
                if type(instruction) is ir.Binop and \
                        type(instruction.a) is ir.Binop and \
                        instruction.a.operation == '+' and \
                        self.is_const(instruction.a.b) and \
                        (instruction.operation == '+') and \
                        self.is_const(instruction.b):
                    # Now we can replace x = (y+5)+5 with x = y + 10
                    a = self.eval_const(instruction.a.b)
                    b = self.eval_const(instruction.b)
                    assert a.ty is b.ty
                    cn = ir.Const(a.value + b.value, 'new_fold', a.ty)
                    block.insert_instruction(
                        cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    assert instruction.ty is cn.ty
                    assert instruction.ty is instruction.a.ty
                    count += 1
                elif type(instruction) is ir.Binop and \
                        type(instruction.a) is ir.Binop and \
                        instruction.a.operation == '-' and \
                        self.is_const(instruction.a.b) and \
                        instruction.operation == '-' and \
                        self.is_const(instruction.b):
                    # Now we can replace x = (y-5)-5 with x = y - 10
                    a = self.eval_const(instruction.a.b)
                    b = self.eval_const(instruction.b)
                    assert a.ty is b.ty
                    cn = ir.Const(a.value + b.value, 'new_fold', a.ty)
                    block.insert_instruction(
                        cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    assert instruction.ty is cn.ty
                    assert instruction.ty is instruction.a.ty
                    count += 1
        if count > 0:
            self.logger.debug('Folded {} expressions'.format(count))


class CommonSubexpressionEliminationPass(BlockPass):
    """ Replace common sub expressions with the previously defined one. """
    def on_block(self, block):
        ins_map = {}
        stats = 0
        for i in block:
            if isinstance(i, ir.Binop):
                k = (i.a, i.operation, i.b, i.ty)
            elif isinstance(i, ir.Const):
                k = (i.value, i.ty)
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
        count = 0
        instructions = list(block.instructions)
        for instruction in instructions:
            if isinstance(instruction, ir.Value) \
                    and type(instruction) is not ir.Call:
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
    def find_store_backwards(self, i, ty, stop_on=[ir.Call, ir.Store]):
        """ Go back from this instruction to beginning """
        block = i.block
        instructions = block.instructions
        pos = instructions.index(i)
        for x in range(pos - 1, 0, -1):
            i2 = instructions[x]
            if type(i2) is ir.Store and ty is i2.value.ty:
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
            self.logger.debug('Replaced {} loads after store'.format(count))

    def remove_redundant_stores(self, block):
        """ From two stores to the same address remove the previous one """
        store_instructions = [
            i for i in block if isinstance(i, ir.Store) and not i.volatile]

        count = 0
        # TODO: assume volatile memory stores always!
        # Replace stores to the same location:
        for store in store_instructions:
            store_prev = self.find_store_backwards(
                store, store.value.ty, stop_on=[ir.Call, ir.Store, ir.Load])
            if store_prev is not None and not store_prev.volatile:
                store_prev.remove_from_block()

        if count > 0:
            self.logger.debug('Replaced {} redundant stores'.format(count))


class CleanPass(FunctionPass):
    """ Glue blocks together if a block has only one predecessor.


        Remove blocks with a single jump in it.

            .. code::

            jump A
            A:
            jump B
            B:

            Transforms into:

            .. code::

            jump B
            B:

    """
    def on_function(self, function):
        self.remove_empty_blocks(function)
        self.remove_one_preds(function)

    def find_empty_blocks(self, function):
        """ Look for all blocks containing only a jump in it """
        empty_blocks = []
        for block in function:
            if block in function.special_blocks:
                continue
            if isinstance(block.first_instruction, ir.Jump):
                empty_blocks.append(block)
        return empty_blocks

    def remove_empty_blocks(self, function):
        """ Remove empty basic blocks from function. """
        stat = 0
        for block in self.find_empty_blocks(function):
            predecessors = block.predecessors
            successors = block.successors

            # Do not remove if preceeded by itself:
            if block in predecessors:
                continue

            # Update successor incoming blocks:
            for successor in successors:
                successor.replace_incoming(block, predecessors)

            # Change the target of predecessors:
            tgt = block.last_instruction.target
            for pred in predecessors:
                pred.change_target(block, tgt)

            # Remove block:
            block.last_instruction.delete()
            function.remove_block(block)
            stat += 1
        if stat > 0:
            self.logger.debug('Removed {} empty blocks'.format(stat))

    def find_single_predecessor_block(self, function):
        """ Find a block with a single predecessor """
        for block in function:
            preds = block.predecessors

            # Check for amount of predecessors:
            if len(preds) != 1:
                continue

            # We have only one predessor:
            pred = preds[0]

            # Skip loops to self:
            if block is pred:
                continue

            # Skip entry and epilog related blocks:
            if block in function.special_blocks:
                continue

            if pred in function.special_blocks:
                continue

            if type(pred.last_instruction) is ir.Jump:
                return block

    def remove_one_preds(self, function):
        """ Remove basic blocks with only one predecessor """
        change = True
        while change:
            change = False
            block = self.find_single_predecessor_block(function)
            if block is not None:
                preds = block.predecessors
                self.glue_blocks(preds[0], block)
                change = True
                # TODO: break, do this only once for now..
                break

    def glue_blocks(self, block1, block2):
        """ Glue two blocks together into the first block """
        self.logger.debug(
            'Inserting {1} at the end of {0}'.format(block1.name, block2.name))

        # Remove the last jump:
        block1.remove_instruction(block1.last_instruction)

        # Copy all instructions to block1:
        for instruction in block2:
            block1.add_instruction(instruction)

        # Replace incoming info:
        for successor in block2.successors:
            successor.replace_incoming(block2, [block1])

        # Remove block from function:
        block1.function.remove_block(block2)
