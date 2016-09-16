
from ...pcc.recursivedescent import RecursiveDescentParser
from .lexer import LlvmIrLexer
from . import nodes


class LlvmIrParser(RecursiveDescentParser):
    """ Recursive descent parser for llvm-ir

    Closely modeled after LLParser.cpp
    """

    def parse_module(self):
        """ Parse a module """
        while not self.at_end:
            if self.peak == 'define':
                self.parse_function()
            else:  # pragma: no cover
                raise NotImplementedError(str(self.peak))

    def parse_function(self):
        """ Parse a function """
        self.consume('define')
        self.parse_type()
        name = self.parse_name(global_name=True)
        self.parse_arg_list()
        self.consume('{')
        while self.peak != '}':
            self.parse_basic_block()
        self.consume('}')
        print(name)

    def parse_basic_block(self):
        if self.peak == 'LBL':
            label = self.consume('LBL')

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
            typ = self.consume('type')
        elif self.peak == '<':
            typ = self.parse_array_type()
        else:
            raise NotImplementedError(self.peak)

        # Parse suffix:
        while True:
            if self.peak == '*':
                self.consume('*')
                typ = ('ptr', typ)
            else:
                break
        print(typ)
        return typ

    def parse_array_type(self):
        self.consume('<')
        size = self.parse_number()
        self.consume('x')
        ty = self.parse_type()
        self.consume('>')
        return size, ty

    def parse_number(self):
        return self.consume('NUMBER').val

    def parse_name(self, global_name=False):
        if global_name:
            return self.consume('GID').val
        else:
            return self.consume('LID').val

    def parse_value(self):
        if self.peak == 'zeroinitializer':
            self.consume('zeroinitializer')
            return 0
        elif self.peak == 'LID':
            return self.parse_name()
        elif self.peak == 'NUMBER':
            return self.consume('NUMBER').val
        else:
            raise NotImplementedError(str(self.peak))

    def parse_type_and_value(self):
        ty = self.parse_type()
        val = self.parse_value()
        return ty, val

    def parse_instruction(self):
        """ Parse an instruction """
        if self.peak == 'LID':
            instruction = self.parse_value_assignment()
        elif self.peak == 'store':
            instruction = self.parse_store()
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
        elif self.peak == 'mul':
            self.consume('mul')
            self.parse_type()
            arg = self.parse_name()
            while self.has_consumed(','):
                arg = self.parse_name()
        else:
            raise NotImplementedError(str(self.peak))
        value.name = name
        return value

    def parse_alloca(self):
        self.consume('alloca')
        ty = self.parse_type()
        size = 0
        alignment = 0
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

    def parse_load(self):
        self.consume('load')
        self.parse_type()
        self.consume(',')
        self.parse_type_and_value()
        return nodes.LoadInst()

    def parse_store(self):
        self.consume('store')
        val = self.parse_type_and_value()
        self.consume(',')
        ptr = self.parse_type_and_value()
        return nodes.StoreInst(val, ptr)

    def parse_ret(self):
        self.consume('ret')
        self.parse_type()
        arg = self.parse_name()
        print('ret', arg)

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


class LlvmIrFrontend:
    def __init__(self):
        self.lexer = LlvmIrLexer()
        self.parser = LlvmIrParser()

    def compile(self, f):
        src = f.read()
        tokens = self.lexer.tokenize(src, eof=True)
        self.parser.init_lexer(tokens)
        self.parser.parse_module()
