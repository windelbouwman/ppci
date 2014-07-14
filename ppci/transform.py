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


class BasicBlockPass(FunctionPass):
    def onFunction(self, f):
        for bb in f.Blocks:
            self.onBasicBlock(bb)

    def onBasicBlock(self, bb):
        """ Override this virtual method """
        raise NotImplementedError()


class InstructionPass(BasicBlockPass):
    def onBasicBlock(self, bb):
        for ins in iter(bb.Instructions):
            self.onInstruction(ins)

    def onInstruction(self, ins):
        """ Override this virtual method """
        raise NotImplementedError()


class BasePass(BasicBlockPass):
    def onBasicBlock(self, bb):
        pass


# Usefull transforms:
class ConstantFolder(BasePass):
    def __init__(self):
        super().__init__()
        self.ops = {}
        self.ops['+'] = lambda x, y: x + y
        self.ops['-'] = lambda x, y: x - y
        self.ops['*'] = lambda x, y: x * y
        self.ops['<<'] = lambda x, y: x << y

    def postExpr(self, expr):
        if type(i) is BinaryOperator and i.operation in self.ops.keys() and type(i.a) is Const and type(i.b) is Const:
            vr = self.ops[i.operation](i.a.value, i.b.value)
            return Const(vr)
        else:
            return expr


class DeadCodeDeleter(BasicBlockPass):
    def onBasicBlock(self, bb):
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


class CommonSubexpressionElimination(BasicBlockPass):
    def onBasicBlock(self, bb):
        constMap = {}
        to_remove = []
        for i in bb.Instructions:
            if isinstance(i, ImmLoad):
                if i.value in constMap:
                    t_new = constMap[i.value]
                    t_old = i.target
                    logging.debug('Replacing {} with {}'.format(t_old, t_new))
                    t_old.replaceby(t_new)
                    to_remove.append(i)
                else:
                    constMap[i.value] = i.target
            elif isinstance(i, BinaryOperator):
                k = (i.value1, i.operation, i.value2)
                if k in constMap:
                    t_old = i.result
                    t_new = constMap[k]
                    logging.debug('Replacing {} with {}'.format(t_old, t_new))
                    t_old.replaceby(t_new)
                    to_remove.append(i)
                else:
                    constMap[k] = i.result
        for i in to_remove:
            self.logger.debug('removing {}'.format(i))
            bb.removeInstruction(i)


child_nodes = {}
child_nodes[ir.Binop] = ['a', 'b']
child_nodes[ir.Add] = ['a', 'b']
child_nodes[ir.Const] = []
child_nodes[ir.Exp] = ['e']
child_nodes[ir.Addr] = ['e']
child_nodes[ir.GlobalVariable] = []
child_nodes[ir.Parameter] = []
child_nodes[ir.Jump] = []
child_nodes[ir.Terminator] = []
child_nodes[ir.Call] = ['arguments']
child_nodes[ir.CJump] = ['a', 'b']


def apply_function(x, f):
    """ Recursively apply function """
    # Handle list:
    if type(x) is list:
        for i in range(len(x)):
            x[i] = apply_function(x[i], f)
        return x

    # Normal node:
    for child in child_nodes[type(x)]:
        v = getattr(x, child)
        v = apply_function(v, f)
        assert not (v is None)
        setattr(x, child, v)
    # Apply function!
    return f(x)


class ExpressionFixer(InstructionPass):
    def onInstruction(self, i):
        apply_function(i, self.grok)


class RemoveAddZero(ExpressionFixer):
    def grok(self, v):
        if type(v) is ir.Binop:
            if v.operation == '+':
                if type(v.b) is ir.Const and v.b.value == 0:
                    self.logger.debug('Folding {} to {}'.format(v, v.a))
                    return v.a
            elif v.operation == '*':
                if type(v.b) is ir.Const and v.b.value == 1:
                    self.logger.debug('Multiple 1 {} to {}'.format(v, v.a))
                    return v.a
        return v


class CleanPass(FunctionPass):
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
