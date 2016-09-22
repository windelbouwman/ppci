
""" LLVM-ir nodes """


class Value:
    """ Root of most nodes """
    def __init__(self, ty):
        self.ty = ty


class BasicBlock(Value):
    """ A sequence of non-interrupted instructions """
    def __init__(self, label, instructions):
        self.label = label
        self.instructions = instructions


class User(Value):
    pass


class Instruction(User):
    @property
    def is_terminator(self):
        return isinstance(self, TerminatorInst)


class BinaryOperator(Instruction):
    @staticmethod
    def create(op, lhs, rhs):
        return BinaryOperator()


class CmpInst(Instruction):
    pass


class FCmpInst(CmpInst):
    pass


class ICmpInst(CmpInst):
    pass


class ExtractElementInst(Instruction):
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2


class GetElementPtrInst(Instruction):
    def __init__(self, ty, ptr, indices):
        self.ty = ty


class InsertElementInst(Instruction):
    def __init__(self, op1, op2, op3):
        self.op1 = op1
        self.op2 = op2


class PhiNode(Instruction):
    pass


class SelectInst(Instruction):
    pass


class ShuffleVectorInst(Instruction):
    def __init__(self, op1, op2, op3):
        self.op1 = op1
        self.op2 = op2


class StoreInst(Instruction):
    def __init__(self, val, ptr):
        self.val = val
        self.ptr = ptr


class TerminatorInst(Instruction):
    pass


class BranchInst(TerminatorInst):
    pass


class CallInst(Instruction):
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


void_ty_id = 0
half_ty_id = 1
float_ty_id = 2
double_ty_id = 3
integer_ty_id = 11
array_ty_id = 14
pointer_ty_id = 15
vector_ty_id = 16


class Type:
    def __init__(self, context, type_id):
        self.context = context
        self.type_id = type_id

    @property
    def is_void(self):
        return self.type_id == void_ty_id

    @staticmethod
    def get_void_ty(context):
        return context.void_ty


class IntegerType(Type):
    def __init__(self, context, bits):
        super().__init__(context, integer_ty_id)
        self.bits = bits

    @staticmethod
    def get(context, num_bits):
        """ Get the integer type with the given number of bits """
        if num_bits not in context.integer_types:
            context.integer_types[num_bits] = IntegerType(context, num_bits)
        return context.integer_types[num_bits]


class CompositeType(Type):
    pass


class SequentialType(CompositeType):
    pass


class PointerType(SequentialType):
    def __init__(self, pointed_type):
        self.pointed_type = pointed_type


class ArrayType(SequentialType):
    def __init__(self, context, elmty, num):
        super().__init__(context, array_ty_id)
        self.num = num

    @staticmethod
    def get(elmty, num):
        context = elmty.context
        return ArrayType(context, elmty, num)


class VectorType(SequentialType):
    def __init__(self, context, elmty, num):
        super().__init__(context, vector_ty_id)
        self.num = num

    @staticmethod
    def get(elmty, num):
        context = elmty.context
        return VectorType(context, elmty, num)


class Context:
    """ LLVM context """
    def __init__(self):
        self.void_ty = Type(self, void_ty_id)
        self.double_ty = Type(self, double_ty_id)
        self.int1_ty = IntegerType(self, 1)
        self.int8_ty = IntegerType(self, 8)
        self.int16_ty = IntegerType(self, 16)
        self.int32_ty = IntegerType(self, 32)
        self.int64_ty = IntegerType(self, 64)
        self.int128_ty = IntegerType(self, 128)
        self.vector_types = []
        self.integer_types = {
            1: self.int1_ty,
            8: self.int8_ty,
            16: self.int16_ty,
            32: self.int32_ty,
            64: self.int64_ty,
            128: self.int128_ty,
            }
