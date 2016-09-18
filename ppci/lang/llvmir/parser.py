
from ...pcc.recursivedescent import RecursiveDescentParser
from . import nodes


class LlvmIrParser(RecursiveDescentParser):
    """ Recursive descent parser for llvm-ir

    Closely modeled after LLParser.cpp
    """
    def __init__(self, context):
        super().__init__()
        self.context = context

    def parse_module(self):
        """ Parse a module """
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

    def parse_define(self):
        """ Parse a function """
        self.consume('define')
        name = self.parse_function_header()
        self.consume('{')
        while self.peak != '}':
            self.parse_basic_block()
        self.consume('}')
        print(name)

    def parse_declare(self):
        """ Parse a function declaration """
        self.consume('declare')
        name = self.parse_function_header()
        print(name)

    def parse_function_header(self):
        self.parse_type()
        name = self.parse_name(global_name=True)
        self.parse_arg_list()
        if self.peak == 'ATTRID':
            self.consume('ATTRID')
        return name

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
        print('target', val)
        return val

    def parse_unnamed_attr_group(self):
        self.consume('attributes')
        attr_id = self.consume('ATTRID')
        self.consume('=')
        self.consume('{')
        self.parse_function_attribute_pairs()
        self.consume('}')
        return attr_id

    def parse_function_attribute_pairs(self):
        attributes = []
        while True:
            if self.peak in ['nounwind', 'sspstrong', 'uwtable']:
                self.consume()
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

        # Parse instructions until terminator
        instructions = []
        while True:
            instruction = self.parse_instruction()
            instructions.append(instruction)
            if instruction.is_terminator:
                break
        return nodes.BasicBlock(label, instructions)

    def parse_arg_list(self):
        """ Parse '(' ... ')' """
        self.consume('(')
        args = []
        if self.peak == ')':
            pass
        else:
            arg = self.parse_arg()
            args.append(arg)
            while self.has_consumed(','):
                arg = self.parse_arg()
                args.append(arg)
        self.consume(')')
        return args

    def parse_arg(self):
        typ = self.parse_type()
        if self.peak == 'LID':
            name = self.consume('LID')
        else:
            name = None
        return (typ, name)

    def parse_type(self):
        if self.peak == 'type':
            typ = self.consume('type').val
        elif self.peak == '[':
            typ = self.parse_array_vector_type(False)
        elif self.peak == '<':
            typ = self.parse_array_vector_type(True)
        else:
            raise NotImplementedError(self.peak)

        # Parse suffix:
        while True:
            if self.peak == '*':
                self.consume('*')
                typ = nodes.PointerType(typ)
            else:
                break
        print(typ)
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

    def parse_value(self, ty=None):
        """ Parse a value with a certain type """
        if self.peak == 'zeroinitializer':
            self.consume('zeroinitializer')
            return 0
        elif self.peak == 'LID':
            return self.parse_name()
        elif self.peak == 'GID':
            return self.parse_name(global_name=True)
        elif self.peak == 'NUMBER':
            return self.consume('NUMBER').val
        else:
            raise NotImplementedError(str(self.peak))

    def parse_type_and_value(self):
        ty = self.parse_type()
        val = self.parse_value(ty)
        return val

    def parse_instruction(self):
        """ Parse an instruction """
        if self.peak == 'LID':
            instruction = self.parse_value_assignment()
        elif self.peak == 'store':
            instruction = self.parse_store()
        elif self.peak == 'call':
            instruction = self.parse_call()
        elif self.peak == 'ret':
            instruction = self.parse_ret()
        else:  # pragma: no cover
            raise NotImplementedError(str(self.peak))
        print(instruction)
        return instruction

    def parse_value_assignment(self):
        """ Parse assignment to an ssa value """
        name = self.parse_name()
        self.consume('=')
        print(name, '=')
        if self.peak == 'alloca':
            value = self.parse_alloca()
        elif self.peak == 'load':
            value = self.parse_load()
        elif self.peak == 'extractelement':
            value = self.parse_extract_element()
        elif self.peak == 'shufflevector':
            value = self.parse_shuffle_vector()
        elif self.peak in ['mul', 'add', 'sub']:
            value = self.parse_arithmatic()
        elif self.peak == 'getelementptr':
            value = self.parse_getelementptr()
        else:
            raise NotImplementedError(str(self.peak))
        value.name = name
        return value

    def parse_arithmatic(self):
        op = self.consume('mul')
        lhs = self.parse_type_and_value()
        self.consume(',')
        rhs = self.parse_value()
        return nodes.BinaryOperator.create(op, lhs, rhs)

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
        self.parse_type()
        self.consume(',')
        self.parse_type_and_value()
        if self.has_consumed(','):
            self.consume('align')
            self.parse_number()
        return nodes.LoadInst()

    def parse_store(self):
        self.consume('store')
        val = self.parse_type_and_value()
        self.consume(',')
        ptr = self.parse_type_and_value()
        return nodes.StoreInst(val, ptr)

    def parse_getelementptr(self):
        self.consume('getelementptr')
        inbounds = self.has_consumed('inbounds')
        ty = self.parse_type()
        self.consume(',')
        ptr = self.parse_type_and_value()
        indices = []
        while self.has_consumed(','):
            val = self.parse_type_and_value()
            indices.append(val)
        return nodes.GetElementPtrInst(ty, ptr, indices)

    def parse_call(self):
        self.consume('call')
        ret_type = self.parse_type()
        name = self.parse_name(global_name=True)
        args = self.parse_parameter_list()
        return nodes.CallInst()

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
        self.consume('ret')
        ty = self.parse_type()
        if ty.is_void:
            return nodes.ReturnInst()
        else:
            arg = self.parse_value()
            print('ret', arg)
            return nodes.ReturnInst()

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
