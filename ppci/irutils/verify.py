""" Verify an IR-module for consistency.

This is a very useful module since it allows to isolate
bugs in the compiler itself.
"""

import logging
from collections import defaultdict
from ..graph.domtree import CfgInfo
from ..common import IrFormError
from .. import ir


def verify_module(module: ir.Module):
    """ Check if the module is properly constructed

    Args:
        module: The module to verify.
    """
    Verifier().verify(module)


class Verifier:
    """ Checks an ir module for correctness """

    logger = logging.getLogger("verifier")

    def __init__(self):
        self.name_map = {}

    def verify(self, module):
        """ Verifies a module for some sanity """
        self.logger.debug("Verifying %s", module)
        assert isinstance(module, ir.Module)
        for function in module.functions:
            self.verify_function(function)

    def verify_function(self, function):
        """ Verify all blocks in the function """
        self.name_map = {}
        for block in function:
            assert block.name not in self.name_map
            self.name_map[block.name] = block
            self.verify_block_termination(block)
            if isinstance(block.last_instruction, ir.Return):
                assert isinstance(function, ir.Function)
                if block.last_instruction.result.ty is not function.return_ty:
                    raise IrFormError(
                        "Last instruction returns {}, while function {}"
                        "returns {}".format(
                            block.last_instruction.result.ty,
                            function,
                            function.return_ty,
                        )
                    )
            elif isinstance(block.last_instruction, ir.Exit):
                assert isinstance(function, ir.Procedure)

        # Verify the entry is in this function and is the first block:
        assert function.entry is function.blocks[0]
        assert isinstance(function.entry, ir.Block)

        # Verify all blocks are reachable:
        reachable_blocks = function.calc_reachable_blocks()
        for block in function:
            assert block in reachable_blocks

        # Determine predecessors from sucessors:
        predecessor_map = defaultdict(set)
        for block in function:
            for block2 in block.successors:
                predecessor_map[block2].add(block)

        # Verify predecessor and successor:
        for block in function:
            preds = predecessor_map[block]
            assert preds == set(block.predecessors)

        # Check that phi's have inputs for each predecessor:
        for block in function:
            for phi in block.phis:
                for predecessor in block.predecessors:
                    used_value = phi.get_value(predecessor)
                    # Check that phi 'use' info is good:
                    assert used_value in phi.uses

        # Now we can build a dominator tree
        self.cfg_info = CfgInfo(function)

        for block in function:
            assert block.function is function
            self.verify_block(block)

    def verify_block_termination(self, block):
        """ Verify that the block is terminated correctly """
        if block.is_empty:
            raise ValueError("Block is empty: {}".format(block))
        if not block.last_instruction.is_terminator:
            raise ValueError(
                "The last instruction of {} is not a terminator instruction".format(
                    block
                )
            )
        assert all(not i.is_terminator for i in block.instructions[:-1])
        assert all(isinstance(p, ir.Block) for p in block.predecessors)

    def verify_block(self, block):
        """ Verify block for correctness """
        for instruction in block:
            self.verify_instruction(instruction, block)

    def verify_instruction(self, instruction, block):
        """ Verify that instruction belongs to block and that all uses
            are preceeded by defs """

        # Check that instruction is contained in block:
        assert instruction.block == block
        assert instruction in block.instructions

        # Check if value has unique name string:
        if isinstance(instruction, ir.Value):
            assert instruction.name not in self.name_map
            self.name_map[instruction.name] = instruction

        if isinstance(instruction, ir.Binop):
            # Check that binop operands are of same type:
            if instruction.ty is not instruction.a.ty:
                raise TypeError(
                    "Binary operand a's type ({}) is not {}".format(
                        instruction.a.ty, instruction.ty
                    )
                )
            if instruction.ty is not instruction.b.ty:
                raise TypeError(
                    "Binary operand b's type({}) is not {}".format(
                        instruction.b.ty, instruction.ty
                    )
                )
        elif isinstance(instruction, ir.Load):
            if instruction.address.ty is not ir.ptr:
                raise TypeError(
                    "Load instruction requires ptr type, not {}".format(
                        instruction.address.ty
                    )
                )
        elif isinstance(instruction, ir.Store):
            if instruction.address.ty is not ir.ptr:
                raise TypeError(
                    "Store instruction requires ptr type, not {}".format(
                        instruction.address.ty
                    )
                )
        elif isinstance(instruction, ir.Phi):
            for inp_val in instruction.inputs.values():
                assert instruction.ty is inp_val.ty
        elif isinstance(instruction, ir.CJump):
            if instruction.a.ty is not instruction.b.ty:
                raise IrFormError(
                    "Type {} is not {} in {}".format(
                        instruction.a.ty, instruction.b.ty, instruction
                    )
                )
        elif isinstance(instruction, (ir.FunctionCall, ir.ProcedureCall)):
            if isinstance(
                instruction.callee, (ir.SubRoutine, ir.ExternalSubRoutine)
            ):
                self.verify_subroutine_call(instruction)

        # Verify that all uses are defined before this instruction.
        for value in instruction.uses:
            assert self.instruction_dominates(
                value, instruction
            ), "{} does not dominate {}".format(value, instruction)

            # Check that a value is not undefined:
            if isinstance(value, ir.Undefined):
                self.logger.warning(
                    "Undefined value '{}' is used".format(value)
                )
                # TODO: usage of undefined data is not good
                # raise error or warning here?
                # To enable compilation with optimization, this occurs
                # frequently in the case of many c programs.
                # raise IrFormError("{} is used".format(value))

    def verify_subroutine_call(self, instruction):
        """ Check some properties of a function call """
        # Check if we called function or procedure:
        callee = instruction.callee
        if isinstance(instruction, ir.FunctionCall):
            if not isinstance(callee, (ir.Function, ir.ExternalFunction)):
                raise IrFormError(
                    "{} expected a function, but got: {}".format(
                        instruction, callee
                    )
                )

            # Check return type:
            if callee.return_ty is not instruction.ty:
                raise IrFormError(
                    "Function returns {}, expected {}".format(
                        callee.return_ty, instruction.ty
                    )
                )
        else:
            if not isinstance(callee, (ir.Procedure, ir.ExternalProcedure)):
                raise IrFormError(
                    "{} expected a procedure, got: {}".format(
                        instruction, callee
                    )
                )

        # Check arguments:
        passed_types = [a.ty for a in instruction.arguments]
        if isinstance(callee, ir.SubRoutine):
            arg_types = [a.ty for a in callee.arguments]
        else:
            arg_types = callee.argument_types
        name = instruction.callee.name

        # Check amount of arguments:
        if len(passed_types) != len(arg_types):
            raise IrFormError(
                "{} expects {} arguments, but called with {}".format(
                    name, len(arg_types), len(passed_types)
                )
            )

        for passed_type, arg_type in zip(passed_types, arg_types):
            if passed_type is not arg_type:
                raise IrFormError(
                    "{} expects {}, but got {}".format(
                        name, arg_type, passed_type
                    )
                )

    def instruction_dominates(self, one, another):
        """ Checks if one instruction dominates another instruction """
        if isinstance(one, (ir.Parameter, ir.GlobalValue)):
            # TODO: hack, parameters and globals dominate all other
            # instructions..
            return True

        # All other instructions must have a containing block:
        if one.block is None:
            raise ValueError("{} has no block".format(one))
        assert one in one.block.instructions

        # Phis are special case:
        if isinstance(another, ir.Phi):
            for block in another.inputs:
                if another.inputs[block] is one:
                    # This is the queried dominance branch
                    # Check if this instruction dominates the last
                    # instruction of this block
                    return self.instruction_dominates(
                        one, block.last_instruction
                    )
            raise RuntimeError(
                "Cannot query dominance for this phi"
            )  # pragma: no cover
        else:
            # For all other instructions follow these rules:
            if one.block is another.block:
                return one.position < another.position
            else:
                return self.block_dominates(one.block, another.block)

    def block_dominates(self, one: ir.Block, another: ir.Block):
        """ Check if this block dominates other block """
        assert one in one.function
        one_node = self.cfg_info.get_node(one)
        another_node = self.cfg_info.get_node(another)
        return self.cfg_info.cfg.strictly_dominates(one_node, another_node)
