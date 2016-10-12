
from collections import namedtuple
import logging
from ...pcc.recursivedescent import RecursiveDescentParser
from . import nodes


class LlvmIrParser(RecursiveDescentParser):
    """ Recursive descent parser for llvm-ir

    Closely modeled after LLParser.cpp at:
    https://github.com/llvm-mirror/llvm/blob/master/lib/AsmParser/LLParser.cpp
    """
    logger = logging.getLogger('llvm-parse')

    def __init__(self, context):
        super().__init__()
        self.context = context
        self._pfs = None
        self.module = None
        self.numbered_vals = []

    def parse_module(self):
        """ Parse a module """
        self.logger.debug('Parsing module')
        self.module = nodes.Module(self.context)
        while not self.at_end:
            if self.peak == 'define':
                self.parse_define()
            elif self.peak == 'declare':
                self.parse_declare()
            elif self.peak == 'target':
                self.parse_target_definition()
            elif self.peak == 'attributes':
                self.parse_unnamed_attr_group()
            elif self.peak == 'MDVAR':
                self.parse_named_metadata()
            elif self.peak == '!':
                self.parse_standalone_metadata()
            else:  # pragma: no cover
                raise NotImplementedError(str(self.peak))
        return self.module

    def parse_define(self):
        """ Parse a function """
        self.consume('define')
        function = self.parse_function_header()
        self.parse_function_body(function)

    def parse_function_body(self, function):
        self._pfs = PerFunctionState(self, function)
        self.consume('{')
        while self.peak != '}':
            self.parse_basic_block()
        self.consume('}')
        self._pfs = None

    def parse_declare(self):
        """ Parse a function declaration """
        self.consume('declare')
        function = self.parse_function_header()

    def parse_function_header(self):
        return_type = self.parse_type()
        name = self.parse_name(global_name=True)
        arg_list = self.parse_arg_list()
        attributes = self.parse_fn_attribute_value_pairs()
        param_types = [a.type for a in arg_list]
        if self.peak == 'ATTRID':
            self.consume('ATTRID')
        function_type = nodes.FunctionType.get(return_type, param_types)
        function = nodes.Function.create(function_type, name, self.module)
        for argument, arg_info in zip(function.arguments, arg_list):
            if arg_info.name:
                argument.set_name(arg_info.name)
            else:
                # The parameter had no name, so number it?
                name = '%{}'.format(len(self.numbered_vals))
                argument.set_name(name)
                self.numbered_vals.append((name, argument))
        return function

    def parse_target_definition(self):
        """ Parse a target top level entity """
        self.consume('target')
        if self.peak == 'triple':
            self.consume('triple')
            self.consume('=')
            val = self.parse_string_constant()
        else:
            self.consume('datalayout')
            self.consume('=')
            val = self.parse_string_constant()
            # self.module.data_layout.reset(val)
        return val

    def parse_unnamed_attr_group(self):
        self.consume('attributes')
        attr_id = self.consume('ATTRID')
        self.consume('=')
        self.consume('{')
        attributes = self.parse_fn_attribute_value_pairs()
        self.consume('}')
        return attr_id

    def parse_fn_attribute_value_pairs(self):
        attributes = []
        while True:
            if self.peak in ['nounwind', 'sspstrong', 'uwtable', 'readonly']:
                a = self.consume().val
                attributes.append(a)
            elif self.peak == 'STR':
                key = self.parse_string_constant()
                if self.has_consumed('='):
                    val = self.parse_string_constant()
                else:
                    val = None
                attributes.append((key, val))
            else:
                break
        return attributes

    def parse_named_metadata(self):
        """ Parse meta data starting with '!my.var'  """
        self.consume('MDVAR')
        self.consume('=')
        self.consume('!')
        self.consume('{')
        while self.peak != '}':
            self.consume()
        self.consume('}')

    def parse_standalone_metadata(self):
        """ Parse meta data starting with '!' 'num' """
        self.consume('!')
        self.parse_number()
        self.consume('=')
        self.consume('!')
        self.parse_md_node_vector()

    def parse_md_node_vector(self):
        self.consume('{')
        elements = []
        while self.peak != '}':
            self.consume()
            # TODO: parse meta data!
            #if elements:
            #    self.consume(',')
            #metadata = self.parse_metadata()
            #elements.append(metadata)
        self.consume('}')
        return elements

    def parse_metadata(self):
        """ Parse meta data

        !42
        !{...}
        !"string"

        """
        if self.peak == '!':
            self.consume('!')
        else:
            md = 1
        return md

    def parse_string_constant(self):
        return self.consume('STR').val

    def parse_basic_block(self):
        if self.peak == 'LBL':
            label = self.consume('LBL').val
        else:
            label = None
        bb = self._pfs.define_bb(label)

        # Parse instructions until terminator
        while True:
            if self.peak == 'LID':
                name = self.parse_name()
                self.consume('=')
            else:
                name = None

            instruction = self.parse_instruction()
            bb.instructions.append(instruction)
            if name:
                self._pfs.set_instruction_name(name, instruction)
            if instruction.is_terminator:
                break
        return bb

    def parse_arg_list(self):
        """ Parse '(' ... ')' """
        self.consume('(')
        args = []
        if self.peak == ')':
            pass
        else:
            args.append(self.parse_arg())
            while self.has_consumed(','):
                args.append(self.parse_arg())
        self.consume(')')
        return args

    def parse_arg(self):
        ty = self.parse_type()
        attrs = self.parse_optional_param_attrs()
        if self.peak == 'LID':
            name = self.consume('LID').val
        else:
            name = None
        return ArgInfo(ty, name)

    def parse_optional_param_attrs(self):
        attrs = []
        while True:
            if self.peak in ['nocapture', 'nonnull']:
                attr = self.consume().val
                attrs.append(attr)
            else:
                break
        return attrs

    def parse_type(self):
        if self.peak == 'type':
            typ = self.consume('type').val
        elif self.peak == '[':
            typ = self.parse_array_vector_type(False)
        elif self.peak == '<':
            typ = self.parse_array_vector_type(True)
        else:  # pragma: no cover
            self.not_impl()

        # Parse suffix:
        while True:
            if self.peak == '*':
                self.consume('*')
                typ = nodes.PointerType.get_unequal(typ)
            else:
                break
        return typ

    def parse_array_vector_type(self, is_vector):
        if is_vector:
            self.consume('<')
        else:
            self.consume('[')
        size = self.parse_number()
        self.consume('x')
        ty = self.parse_type()
        if is_vector:
            self.consume('>')
            return nodes.VectorType.get(ty, size)
        else:
            self.consume(']')
            return nodes.ArrayType.get(ty, size)

    def parse_number(self):
        return self.consume('NUMBER').val

    def parse_name(self, global_name=False):
        if global_name:
            return self.consume('GID').val
        else:
            return self.consume('LID').val

    def parse_global_value(self, ty):
        v = self.parse_val_id()
        v2 = self.convert_val_id_to_value(ty, v)
        return v2

    def parse_value(self, ty):
        """ Parse a value with a certain type """
        v = self.parse_val_id()
        v2 = self.convert_val_id_to_value(ty, v)
        return v2

    def parse_val_id(self):
        """ Some more abstract value parsing """
        if self.peak == 'zeroinitializer':
            self.consume('zeroinitializer')
            v = ValId('zero', None)
        elif self.peak == 'LID':
            v = ValId('local', self.parse_name())
        elif self.peak == 'GID':
            v = self.parse_name(global_name=True)
        elif self.peak == 'NUMBER':
            v = ValId('int', self.consume('NUMBER').val)
        elif self.peak == 'HEXDOUBLE':
            v = ValId('float', self.consume('HEXDOUBLE').val)
        elif self.peak == 'undef':
            self.consume('undef')
            v = ValId('undef', None)
        elif self.peak == 'true':
            self.consume('true')
            v = ValId('constant', nodes.ConstantInt.get_true(self.context))
        elif self.peak == 'false':
            self.consume('false')
            v = ValId('constant', nodes.ConstantInt.get_false(self.context))
        elif self.peak == '<':
            # '<' constvect '>'
            self.consume('<')
            elts = self.parse_global_value_vector()
            self.consume('>')
            v = ValId('constant', nodes.ConstantVector.get(elts))
        else:  # pragma: no cover
            self.not_impl()
        assert isinstance(v, ValId)
        return v

    def convert_val_id_to_value(self, ty, val_id):
        if val_id.kind == 'local':
            v = self._pfs.get_val(val_id.val, ty)
        elif val_id.kind == 'int':
            if not ty.is_integer:
                self.error('integer constant must have integer type')
            v = nodes.ConstantInt.get(ty, val_id.val)
        elif val_id.kind == 'float':
            if not ty.is_floating_point:
                self.error('Floating point constant invalid for type')
            v = nodes.ConstantFP.get(ty, val_id.val)
        elif val_id.kind == 'zero':
            v = nodes.Constant.get_null_value(ty)
        elif val_id.kind == 'undef':
            v = nodes.UndefValue.get(ty)
        elif val_id.kind == 'constant':
            v = val_id.val
            if v.ty is not ty:
                self.error('constant expression type mismatch')
        else:
            raise NotImplementedError(str(val_id))
        return v

    def parse_type_and_value(self):
        ty = self.parse_type()
        val = self.parse_value(ty)
        return val

    def parse_type_and_basic_block(self):
        value = self.parse_type_and_value()
        if not isinstance(value, nodes.BasicBlock):
            self.error('Expected a basic block')
        return value

    def parse_global_value_vector(self):
        """ """
        v = []
        v.append(self.parse_global_type_and_value())
        while self.has_consumed(','):
            v.append(self.parse_global_type_and_value())
        return v

    def parse_global_type_and_value(self):
        ty = self.parse_type()
        val = self.parse_global_value(ty)
        return val

    # Instructions
    def parse_instruction(self):
        """ Parse a single instruction """
        if self.peak == 'store':
            instruction = self.parse_store()
        elif self.peak == 'call':
            instruction = self.parse_call()
        elif self.peak == 'ret':
            instruction = self.parse_ret()
        elif self.peak == 'br':
            instruction = self.parse_br()
        elif self.peak == 'alloca':
            instruction = self.parse_alloca()
        elif self.peak == 'load':
            instruction = self.parse_load()
        elif self.peak == 'extractelement':
            instruction = self.parse_extract_element()
        elif self.peak == 'insertelement':
            instruction = self.parse_insert_element()
        elif self.peak == 'shufflevector':
            instruction = self.parse_shuffle_vector()
        elif self.peak in [
                'add', 'fadd', 'sub', 'fsub', 'mul', 'fmul',
                'udiv', 'sdiv', 'fdiv', 'urem', 'srem',
                'shl', 'lshr', 'ashr']:
            instruction = self.parse_arithmatic()
        elif self.peak in ['and', 'or']:
            instruction = self.parse_arithmatic()
        elif self.peak in [
                'sext', 'zext',
                'trunc', 'fptrunc',
                'uitofp', 'fptoui', 'sitofp', 'fptosi',
                'ptrtoint', 'inttoptr']:
            instruction = self.parse_cast()
        elif self.peak == 'select':
            instruction = self.parse_select()
        elif self.peak in ['icmp', 'fcmp']:
            instruction = self.parse_compare()
        elif self.peak == 'getelementptr':
            instruction = self.parse_getelementptr()
        else:  # pragma: no cover
            self.not_impl()
        return instruction

    def parse_arithmatic(self):
        op = self.consume()
        lhs = self.parse_type_and_value()
        self.consume(',')
        rhs = self.parse_value(lhs.ty)
        return nodes.BinaryOperator.create(op, lhs, rhs)

    def parse_cast(self):
        op = self.consume()
        val = self.parse_type_and_value()
        self.consume('to')
        dest_ty = self.parse_type()
        return nodes.CastInst.create(op, val, dest_ty)

    def parse_select(self):
        self.consume('select')
        op0 = self.parse_type_and_value()
        self.consume(',')
        op1 = self.parse_type_and_value()
        self.consume(',')
        op2 = self.parse_type_and_value()
        return nodes.SelectInst.create(op0, op1, op2)

    def parse_compare(self):
        icmp = self.peak == 'icmp'
        if icmp:
            self.consume('icmp')
        else:
            self.consume('fcmp')
        pred = self.parse_cmp_predicate(icmp)
        lhs = self.parse_type_and_value()
        self.consume(',')
        rhs = self.parse_value(lhs.ty)
        return nodes.ICmpInst(pred, lhs, rhs)

    def parse_cmp_predicate(self, icmp):
        if icmp:
            predicates = {
                'eq': nodes.CmpInst.ICMP_EQ,
                'ne': nodes.CmpInst.ICMP_NE,
                'slt': nodes.CmpInst.ICMP_SLT,
                'sgt': nodes.CmpInst.ICMP_SGT,
                'sle': nodes.CmpInst.ICMP_SLE,
                'sge': nodes.CmpInst.ICMP_SGE,
                'ult': nodes.CmpInst.ICMP_ULT,
                'ugt': nodes.CmpInst.ICMP_UGT,
                'ule': nodes.CmpInst.ICMP_ULE,
                'uge': nodes.CmpInst.ICMP_UGE,
            }
        else:
            predicates = {
                'ueq': nodes.CmpInst.FCMP_UEQ,
            }
        if self.peak in predicates:
            v = self.consume().val
            return predicates[v]
        else:
            self.error('Expected one of {}'.format(predicates.keys()))

    def parse_alloca(self):
        self.consume('alloca')
        ty = self.parse_type()
        size = 0
        alignment = 0
        if self.peak == ',':
            self.consume(',')
            self.consume('align')
            self.parse_number()
        return nodes.AllocaInst(ty, size, alignment)

    def parse_extract_element(self):
        self.consume('extractelement')
        op1 = self.parse_type_and_value()
        self.consume(',')
        op2 = self.parse_type_and_value()
        return nodes.ExtractElementInst(op1, op2)

    def parse_insert_element(self):
        self.consume('insertelement')
        op1 = self.parse_type_and_value()
        self.consume(',')
        op2 = self.parse_type_and_value()
        self.consume(',')
        op3 = self.parse_type_and_value()
        return nodes.InsertElementInst(op1, op2, op3)

    def parse_shuffle_vector(self):
        self.consume('shufflevector')
        op1 = self.parse_type_and_value()
        self.consume(',')
        op2 = self.parse_type_and_value()
        self.consume(',')
        op3 = self.parse_type_and_value()
        return nodes.ShuffleVectorInst(op1, op2, op3)

    def parse_load(self):
        """ Parse load instruction

        'load' 'volatile'? typeandvalue (',' 'align' i32)?
        """
        self.consume('load')
        atomic = self.has_consumed('atomic')
        volatile = self.has_consumed('volatile')
        ty = self.parse_type()
        self.consume(',')
        val = self.parse_type_and_value()
        if self.has_consumed(','):
            self.consume('align')
            self.parse_number()
        return nodes.LoadInst(ty)

    def parse_store(self):
        self.consume('store')
        val = self.parse_type_and_value()
        self.consume(',')
        ptr = self.parse_type_and_value()
        if self.has_consumed(','):
            self.consume('align')
            self.parse_number()
        return nodes.StoreInst(val, ptr)

    def parse_getelementptr(self):
        """ parse the get element ptr (GEP) """
        self.consume('getelementptr')
        inbounds = self.has_consumed('inbounds')
        ty = self.parse_type()
        self.consume(',')
        ptr = self.parse_type_and_value()
        indices = []
        while self.has_consumed(','):
            val = self.parse_type_and_value()
            indices.append(val)
        gep = nodes.GetElementPtrInst(ty, ptr, indices)
        gep.inbounds = inbounds
        return gep

    def parse_call(self):
        self.consume('call')
        ret_type = self.parse_type()
        name = self.parse_name(global_name=True)
        args = self.parse_parameter_list()
        return nodes.CallInst(ret_type)

    def parse_parameter_list(self):
        self.consume('(')
        args = []
        while self.peak != ')':
            if args:
                self.consume(',')
            ty = self.parse_type()
            v = self.parse_value(ty)
            args.append(v)
        self.consume(')')
        return args

    def parse_ret(self):
        """ Parse return instruction """
        self.consume('ret')
        ty = self.parse_type()
        if ty.is_void:
            return nodes.ReturnInst(ty)
        else:
            arg = self.parse_value(ty)
            return nodes.ReturnInst(ty)

    def parse_br(self):
        """ Parse a branch instruction """
        self.consume('br')
        op0 = self.parse_type_and_value()
        if isinstance(op0, nodes.BasicBlock):
            return nodes.BranchInst(op0)
        else:
            self.consume(',')
            op1 = self.parse_type_and_basic_block()
            self.consume(',')
            op2 = self.parse_type_and_basic_block()
            return nodes.BranchInst(op1, op2, op0)

    def parse_phi(self):
        """ Parse a phi instruction.

        For example 'phi' Type '[' Value ',' Value ']' (',' ...) *
        """
        self.parse_type()
        self.consume('[')
        self.parse_value()
        self.consume(',')
        self.parse_value()
        self.consume(']')
        while self.has_consumed(','):
            self.consume('[')
            self.parse_value()
            self.consume(',')
            self.parse_value()
            self.consume(']')


class PerFunctionState:
    """ Keep track of parsing stuff in a function """
    def __init__(self, parser, function):
        self.parser = parser
        self.function = function
        self.forward = {}

    def get_val(self, name, ty):
        """ Get a value with a name and a given type """
        # Lookup the name:
        if name in self.function.vmap:
            val = self.function.vmap[name]
        elif name in self.forward:
            val = self.forward[name]
        else:
            if ty.is_label:
                val = nodes.BasicBlock.create(
                    self.function.context, name, self.function)
            else:
                raise NotImplementedError(str(ty))
            self.forward[name] = val

        if ty is not val.ty:
            self.parser.error('{} != {}'.format(ty, val.ty))
        return val

    def get_bb(self, name):
        return self.get_val(name, self.function.context.label_ty)

    def define_bb(self, name):
        bb = self.get_bb(name)

        # Move basic block from forward to function:
        self.function.basic_blocks.append(bb)
        self.forward.pop(name)
        return bb

    def set_instruction_name(self, name, instruction):
        # This will update the symbol table:
        instruction.set_name(name)

        # Remove placeholder:
        if name in self.forward:
            sentinel = self.forward.pop(name)
            if sentinel.ty is not instruction.ty:
                self.parser.error(
                    'Instruction forward referenced with type {}'.format(
                        sentinel.ty))
            sentinel.replace_all_uses_with(instruction)


ValId = namedtuple('ValId', ['kind', 'val'])
ArgInfo = namedtuple('ArgInfo', ['type', 'name'])
