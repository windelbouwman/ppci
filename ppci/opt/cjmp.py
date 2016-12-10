
import operator
from .transform import InstructionPass
from .. import ir


class CJumpPass(InstructionPass):
    def on_instruction(self, instruction):
        if isinstance(instruction, ir.CJump) and \
                isinstance(instruction.a, ir.Const) and \
                isinstance(instruction.b, ir.Const):
            a = instruction.a.value
            b = instruction.b.value
            mp = {
                '==': operator.eq,
                '<': operator.lt, '>': operator.gt,
                '>=': operator.ge, '<=': operator.le,
                '!=': operator.ne
                }
            if mp[instruction.cond](a, b):
                label = instruction.lab_yes
            else:
                label = instruction.lab_no
            block = instruction.block
            block.remove_instruction(instruction)
            block.add_instruction(ir.Jump(label))
            instruction.delete()
