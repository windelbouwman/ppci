
""" LLVM-ir nodes """


class Value:
    """ Root of most nodes """
    def __init__(self, ty):
        self.ty = ty

    @property
    def context(self):
        return self.ty.context

    def set_name(self, name):
        """ Set name and update symbol table """
        sym_tab = self.symbol_table
        sym_tab[name] = self

    @property
    def symbol_table(self):
        if isinstance(self, Instruction):
            basic_block = self.parent
            function = basic_block.parent
            return function.vmap
        elif isinstance(self, Argument):
            function = self.parent
            return function.vmap
        else:
            raise NotImplementedError(str(self))


class OwnedList(list):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def append(self, x):
        x.parent = self.owner
        super().append(x)


class BasicBlock(Value):
    """ A sequence of non-interrupted instructions """
    def __init__(self, context, label, function):
        super().__init__(context.label_ty)
        self.label = label
        self.instructions = OwnedList(self)
        self.parent = function

    @classmethod
    def create(cls, context, name, function):
        return BasicBlock(context, name, function)


class Argument(Value):
    pass


class UndefValue(Value):
    """ An undefined value """
    @classmethod
    def get(cls, ty):
        return UndefValue(ty)


class User(Value):
    pass


class Constant(User):
    @classmethod
    def get_null_value(cls, ty):
        if ty.type_id == integer_ty_id:
            return ConstantInt.get(ty, 0)
        elif ty.type_id in [vector_ty_id, array_ty_id]:
            return ConstantAggregateZero.get(ty)
        else:  # pragma: no cover
            raise NotImplementedError(str(ty))


class ConstantInt(Constant):
    def __init__(self, ty, value):
        super().__init__(ty)
        self.value = value

    @classmethod
    def get(cls, ty, value):
        return ConstantInt(ty, value)


class ConstantAggregateZero(Constant):
    def __init__(self, ty):
        super().__init__(ty)

    @classmethod
    def get(cls, ty):
        return ConstantAggregateZero(ty)


class ConstantVector(Constant):
    @classmethod
    def get(cls, elts):
        return ConstantVector()


class GlobalValue(Constant):
    pass


class GlobalObject(GlobalValue):
    pass


class Function(GlobalObject):
    def __init__(self, ty):
        super().__init__(ty)
        self.vmap = {}
        self.basic_blocks = OwnedList(self)
        self.arguments = OwnedList(self)
        for param_type in ty.params:
            self.arguments.append(Argument(param_type))

    @classmethod
    def create(cls, function_type, name):
        return Function(function_type)


class Instruction(User):
    @property
    def is_terminator(self):
        return isinstance(self, TerminatorInst)


class BinaryOperator(Instruction):
    def __init__(self, op, lhs, rhs, ty):
        super().__init__(ty)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    @staticmethod
    def create(op, lhs, rhs):
        return BinaryOperator(op, lhs, rhs, lhs.ty)


class CmpInst(Instruction):
    pass


class FCmpInst(CmpInst):
    pass


class ICmpInst(CmpInst):
    def __init__(self, pred, lhs, rhs):
        self.pred = pred
        self.lhs = lhs
        self.rhs = rhs


class ExtractElementInst(Instruction):
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2


class GetElementPtrInst(Instruction):
    def __init__(self, ty, ptr, indices):
        ret_ty = PointerType.get_unequal(ty.el_type)
        super().__init__(ret_ty)
        self.ptr = ptr
        self.indices = indices


class InsertElementInst(Instruction):
    def __init__(self, op1, op2, op3):
        self.op1 = op1
        self.op2 = op2


class PhiNode(Instruction):
    pass


class SelectInst(Instruction):
    def __init__(self, op0, op1, op2):
        super().__init__(op1.ty)
        self.op0 = op0
        self.op1 = op1
        self.op2 = op2

    @classmethod
    def create(cls, op0, op1, op2):
        return SelectInst(op0, op1, op2)


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
    def __init__(self, op1, op2=None, op0=None):
        # super().__init__()
        self.op1 = op1
        self.op2 = op2


class CallInst(Instruction):
    pass


class ReturnInst(TerminatorInst):
    pass


class SwitchInst(TerminatorInst):
    pass


class UnaryInstruction(Instruction):
    pass


class AllocaInst(UnaryInstruction):
    def __init__(self, ty, size, alignment):
        super().__init__(PointerType.get_unequal(ty))
        self.allocated_ty = ty
        self.size = size


class CastInst(Instruction):
    def __init__(self, op, val, dest_ty):
        super().__init__(dest_ty)
        self.op = op
        self.val = val

    @staticmethod
    def create(op, val, dest_ty):
        return CastInst(op, val, dest_ty)


class LoadInst(Instruction):
    pass


void_ty_id = 0
half_ty_id = 1
float_ty_id = 2
double_ty_id = 3
fp128_ty_id = 5
label_ty_id = 7
integer_ty_id = 11
function_ty_id = 12
struct_ty_id = 13
array_ty_id = 14
pointer_ty_id = 15
vector_ty_id = 16


class Type:
    """ The type class """
    def __init__(self, context, type_id):
        self.context = context
        self.type_id = type_id

    @property
    def is_void(self):
        return self.type_id == void_ty_id

    @property
    def is_label(self):
        return self.type_id == label_ty_id

    @property
    def is_integer(self):
        return self.type_id == integer_ty_id

    @staticmethod
    def get_void_ty(context):
        return context.void_ty

    @staticmethod
    def get_label_ty(context):
        return context.label_ty


class FunctionType(Type):
    def __init__(self, result_type, params, is_var_arg=False):
        super().__init__(result_type.context, function_ty_id)
        self.result_type = result_type
        self.params = params

    @classmethod
    def get(cls, result_type, params=(), is_var_arg=False):
        context = result_type.context
        return FunctionType(result_type, params, is_var_arg)


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
    def __init__(self, ty_id, el_type):
        super().__init__(el_type.context, ty_id)
        self.el_type = el_type


class PointerType(SequentialType):
    def __init__(self, pointed_type, address_space):
        super().__init__(pointer_ty_id, pointed_type)

    @classmethod
    def get(cls, ty, address_space):
        context = ty.context
        key = ('pointer', id(ty))
        if key not in context.type_map:
            context.type_map[key] = PointerType(ty, address_space)
        return context.type_map[key]

    @classmethod
    def get_unequal(cls, ty):
        return cls.get(ty, 0)


class ArrayType(SequentialType):
    def __init__(self, elmty, num):
        super().__init__(array_ty_id, elmty)
        self.num = num

    @staticmethod
    def get(elmty, num):
        context = elmty.context
        key = ('array', num, id(elmty))
        if key not in context.type_map:
            context.type_map[key] = ArrayType(elmty, num)
        return context.type_map[key]


class VectorType(SequentialType):
    def __init__(self, elmty, num):
        super().__init__(vector_ty_id, elmty)
        self.num = num

    @staticmethod
    def get(elmty, num):
        context = elmty.context
        key = ('vector', num, id(elmty))
        if key not in context.type_map:
            context.type_map[key] = VectorType(elmty, num)
        return context.type_map[key]


class Context:
    """ LLVM context """
    def __init__(self):
        self.void_ty = Type(self, void_ty_id)
        self.double_ty = Type(self, double_ty_id)
        self.label_ty = Type(self, label_ty_id)
        self.integer_types = {}
        self.int1_ty = IntegerType.get(self, 1)
        self.int8_ty = IntegerType.get(self, 8)
        self.int16_ty = IntegerType.get(self, 16)
        self.int32_ty = IntegerType.get(self, 32)
        self.int64_ty = IntegerType.get(self, 64)
        self.int128_ty = IntegerType.get(self, 128)
        self.vector_types = []
        self.type_map = {}
