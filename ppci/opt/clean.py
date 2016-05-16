
from .transform import FunctionPass
from .. import ir


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
            if block.is_entry:
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
            self.logger.debug('Removed %s empty blocks', stat)

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

            if isinstance(pred.last_instruction, ir.Jump):
                return block

    def remove_one_preds(self, function):
        """ Remove basic blocks with only one predecessor """
        change = True
        while change:
            change = False
            block = self.find_single_predecessor_block(function)
            if block is not None:
                pred, = block.predecessors  # Unpack 1 block
                self.glue_blocks(pred, block)
                change = True

    def glue_blocks(self, block1, block2):
        """ Glue two blocks together into the first block """
        self.logger.debug(
            'Inserting %s at the end of %s', block1.name, block2.name)

        # Remove the last jump:
        last_jump = block1.last_instruction
        block1.remove_instruction(last_jump)
        last_jump.delete()

        # Copy all instructions to block1:
        for instruction in block2:
            block1.add_instruction(instruction)

        # Replace incoming info:
        for successor in block2.successors:
            successor.replace_incoming(block2, [block1])

        # Remove block from function:
        block1.function.remove_block(block2)
