
""" LLVM-ir nodes """


class Module:
    """ Holds all information related to a module """
    def __init__(self, context):
        self.context = context
        self.data_layout = DataLayout()
        self.functions = OwnedList(self)


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
        self.name = name

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
    """ Special list that sets the parent attribute upon append """
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

    @classmethod
    def get_true(cls, context):
        """ Get the constant value for true """
        return cls.get(context.int1_ty, 1)

    @classmethod
    def get_false(cls, context):
        return cls.get(context.int1_ty, 0)


class ConstantFP(Constant):
    def __init__(self, ty, val):
        super().__init__(ty)
        self.val = val

    @classmethod
    def get(cls, ty, val):
        return ConstantFP(ty, val)


class ConstantAggregateZero(Constant):
    def __init__(self, ty):
        super().__init__(ty)

    @classmethod
    def get(cls, ty):
        return ConstantAggregateZero(ty)


class ConstantVector(Constant):
    def __init__(self, elts):
        assert len(elts)
        assert all(e.ty is elts[0].ty for e in elts)
        ty = VectorType.get(elts[0].ty, len(elts))
        super().__init__(ty)
        self.elts = elts

    @classmethod
    def get(cls, elts):
        return ConstantVector(elts)


class GlobalValue(Constant):
    pass


class GlobalObject(GlobalValue):
    pass


class Function(GlobalObject):
    def __init__(self, ty, module):
        super().__init__(ty)
        module.functions.append(self)
        self.vmap = {}
        self.basic_blocks = OwnedList(self)
        self.arguments = OwnedList(self)
        for param_type in ty.params:
            self.arguments.append(Argument(param_type))

    @classmethod
    def create(cls, function_type, name, module):
        return Function(function_type, module)


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
    FCMP_FALSE = 0
    FCMP_OEQ = 1
    FCMP_OGT = 2
    FCMP_OGE = 3
    FCMP_OLT = 4
    FCMP_OLE = 5
    FCMP_ONE = 6
    FCMP_ORD = 7
    FCMP_UNO = 8
    FCMP_UEQ = 9

    FCMP_TRUE = 15

    ICMP_EQ = 32
    ICMP_NE = 33
    ICMP_UGT = 34
    ICMP_UGE = 35
    ICMP_ULT = 36
    ICMP_ULE = 37
    ICMP_SGT = 38
    ICMP_SGE = 39
    ICMP_SLT = 40
    ICMP_SLE = 41

    def __init__(self, pred, lhs, rhs):
        super().__init__(self.make_cmp_result_type(lhs.ty))
        self.pred = pred
        self.lhs = lhs
        self.rhs = rhs

    @classmethod
    def make_cmp_result_type(cls, opnd_type):
        if isinstance(opnd_type, VectorType):
            return VectorType.get(opnd_type.context.int1_ty, opnd_type.num)
        else:
            return opnd_type.context.int1_ty


class FCmpInst(CmpInst):
    pass


class ICmpInst(CmpInst):
    pass


class ExtractElementInst(Instruction):
    def __init__(self, val, index):
        super().__init__(val.ty.el_type)
        self.val = val
        self.index = index


class GetElementPtrInst(Instruction):
    def __init__(self, ty, ptr, indices):
        ret_ty = self.get_gep_return_type(ptr, indices)
        super().__init__(ret_ty)
        self.ptr = ptr
        self.indices = indices

    @staticmethod
    def get_indexed_type(agg, idx_list):
        """ Return the type after all indexing magic """
        for index in idx_list:
            agg = agg.get_type_at_index(index)
        return agg

    @classmethod
    def get_gep_return_type(cls, ptr, idx_list):
        """ Get the pointer type returned by the GEP """
        ty2 = cls.get_indexed_type(ptr.ty, idx_list)
        ptr_ty = PointerType.get(ty2, 0)
        return ptr_ty


class InsertElementInst(Instruction):
    """ Insert element instruction.

    Returns a new vector with element at index replaced.
    """
    def __init__(self, vec, elt, index):
        super().__init__(vec.ty)
        self.vec = vec
        self.elt = elt
        self.index = index


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
    def __init__(self, v1, v2, mask):
        super().__init__(VectorType.get(v1.ty.el_type, mask.ty.num))
        self.v1 = v1
        self.v2 = v2
        self.mask = mask


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

    @property
    def is_floating_point(self):
        return self.type_id in [half_ty_id, float_ty_id, double_ty_id]

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


class StructType(CompositeType):
    def get_type_at_index(self, idx):
        raise NotImplementedError()


class SequentialType(CompositeType):
    def __init__(self, ty_id, el_type):
        super().__init__(el_type.context, ty_id)
        self.el_type = el_type

    def get_type_at_index(self, idx):
        return self.el_type


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
        self.half_ty = Type(self, half_ty_id)
        self.float_ty = Type(self, float_ty_id)
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


class DataLayout:
    def get_type_alloc_size(self, ty):
        pass

    def reset(self, layout_description):
        self.parse_specifier(layout_description)

    def parse_specifier(self, desc):
        for part in desc.split('-'):
            print(part)
            toks = part.split(':')
            if toks[0] == 'e':
                self.big_endian = False
            elif toks[0] == 'E':
                self.big_endian = True
            elif toks[0] == 'm':
                if toks[1] == 'e':
                    self.mangling = 'ELF'
                else:
                    raise NotImplementedError(toks[1])
            else:
                raise NotImplementedError(part)

