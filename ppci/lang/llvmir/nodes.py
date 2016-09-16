
""" LLVM-ir nodes """


class BasicBlock:
    def __init__(self):
        self.instructions = []


class Value:
    pass


class Instruction:
    @property
    def is_terminator(self):
        return isinstance(self, TerminatorInst)


class BinaryOperator(Instruction):
    pass


class CmpInst(Instruction):
    pass


class FCmpInst(CmpInst):
    pass


class ICmpInst(CmpInst):
    pass


class ExtractElementInst(Instruction):
    def __init__(self, op1, op2):
        pass


class GetElementPtrInst(Instruction):
    pass


class PhiNode(Instruction):
    pass


class SelectInst(Instruction):
    pass


class ShuffleVectorInst(Instruction):
    pass


class StoreInst(Instruction):
    def __init__(self, val, ptr):
        self.val = val
        self.ptr = ptr


class TerminatorInst(Instruction):
    pass


class BranchInst(TerminatorInst):
    pass


class ReturnInst(TerminatorInst):
    pass


class SwitchInst(TerminatorInst):
    pass


class AllocaInst(Instruction):
    def __init__(self, ty, size, alignment):
        self.ty = ty
        self.size = size


class CastInst(Instruction):
    pass


class LoadInst(Instruction):
    pass
