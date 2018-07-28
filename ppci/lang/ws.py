
""" Frontend for the whitespace programming language.

Whitespace has only 3 used characters: space (32), tab (9) and newline (10)
See also:

https://en.wikipedia.org/wiki/Whitespace_(programming_language)

http://compsoc.dur.ac.uk/whitespace/tutorial.html
"""

import operator
from ..common import CompilerError


def ws_to_ir(source):
    """ Compile whitespace source """
    return WhitespaceGenerator().compile(source)


class WhitespaceGenerator:
    def compile(self, f):
        prog = WhitespaceParser().compile(f)
        print(prog)
        WhitespaceInterpreter().run(prog)


class WhitespaceRunner:
    """ Run some whitespace source """

    def run(self, f):
        prog = WhitespaceParser().compile(f)
        WhitespaceInterpreter().run(prog)
        print(prog)


class WhitespaceParser:
    """ Parse whitespace sourcecode """

    def __init__(self):
        self.tokens = None
        self.token = None

    def compile(self, f):
        """ Compile whitespace code from open file handle """
        self.start_lexer(f)
        return self.parse_program()

    def start_lexer(self, f):
        self.tokens = self.tokenize(f.read())
        self.token = None
        self.next_token()

    def tokenize(self, txt):
        for c in txt:
            if c in [" ", "\t", "\n"]:
                yield c

    def next_token(self):
        t = self.token
        self.token = next(self.tokens, None)
        return t

    @property
    def peak(self):
        return self.token

    def consume(self, typ):
        """ Eat a token of given type """
        assert self.peak == typ
        return self.next_token()

    def error(self, msg):
        """ Report an error """
        raise CompilerError(msg)

    def has_consumed(self, typ):
        if self.peak == typ:
            self.consume(typ)
            return True
        return False

    def parse_program(self):
        program = []
        while self.peak:
            i = self.parse_instruction()
            print(i)
            program.append(i)
        return program

    def parse_instruction(self):
        """ Parse a new command """
        if self.has_consumed(" "):
            return self.parse_stack_manipulation()
        elif self.has_consumed("\t"):
            if self.has_consumed(" "):
                return self.parse_arithmatic()
            elif self.has_consumed("\t"):
                return self.parse_heap_access()
            elif self.has_consumed("\n"):
                return self.parse_io()
            else:
                self.error("Expected  , \t or \n but got {}".format(self.peak))
        elif self.has_consumed("\n"):
            return self.parse_flow_control()
        else:
            self.error("Expected  , \t or \n but got {}".format(self.peak))

    def parse_stack_manipulation(self):
        if self.has_consumed(" "):
            return Push(self.parse_number())
        else:
            raise NotImplementedError()

    def parse_arithmatic(self):
        """ Parse an arithmatic code """
        if self.has_consumed(" "):
            if self.has_consumed(" "):
                return Add()
            elif self.has_consumed("\t"):
                return Substract()
            elif self.has_consumed("\n"):
                return Multiply()
            else:
                self.error("Expected  , \t or \n")
        elif self.has_consumed("\t"):
            if self.has_consumed(" "):
                return Division()
            elif self.has_consumed("\t"):
                return Modulo()
            else:
                self.error("Expected  or \t")
        else:
            self.error("Expected  or \t")

    def parse_io(self):
        """ Parse io action """
        if self.has_consumed(" "):
            if self.has_consumed(" "):
                return OutputCharacter()
            elif self.has_consumed("\t"):
                return OutputNumber()
            else:
                self.error("Expected  or \t")
        elif self.has_consumed("\t"):
            if self.has_consumed(" "):
                raise NotImplementedError()
            elif self.has_consumed("\t"):
                raise NotImplementedError()
            else:
                self.error("Expected  or \t")
        else:
            raise NotImplementedError()

    def parse_flow_control(self):
        """ Parse flow control constructs """
        if self.has_consumed(" "):
            raise NotImplementedError()
        elif self.has_consumed("\t"):
            raise NotImplementedError()
        elif self.has_consumed("\n"):
            self.consume("\n")
            return EndProgram()
        else:
            self.error("Expected  , \t or \n")

    def parse_number(self):
        """ Parse a number """
        bits = self.parse_bits()
        if len(bits) > 0:
            sign = bits[0]
            v = 0
            for b in bits[1:]:
                v = (v << 1) | b
            if sign:
                v = -v
            return v
        else:
            return 0

    def parse_label(self):
        """ Parse a label """
        self.parse_bits()

    def parse_bits(self):
        """ Parse LF terminated series of bits SP=0, tab=1 """
        bit_values = []
        while not self.has_consumed("\n"):
            if self.has_consumed(" "):
                bit_values.append(0)
            else:
                self.consume("\t")
                bit_values.append(1)
        return bit_values


class Push:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "Push({})".format(self.value)

    def execute(self, context):
        context.stack.append(self.value)


class Binop:
    def execute(self, context):
        a = context.stack.pop(-1)
        b = context.stack.pop(-1)
        context.stack.append(self.op(a, b))


class Add(Binop):
    op = operator.add


class Substract:
    op = operator.sub


class Multiply:
    op = operator.mul


class Division:
    op = operator.floordiv


class Modulo:
    op = operator.mod


class OutputCharacter:
    def execute(self, context):
        char = chr(context.stack[-1])
        print(char, end="")


class OutputNumber:
    pass


class EndProgram:
    def execute(self, context):
        context.running = False


class WhitespaceContext:
    def __init__(self):
        self.stack = []
        self.call_stack = []
        self.pc = 0
        self.running = True


class WhitespaceInterpreter:
    """ Interpreter for the whitespace language """

    def run(self, program):
        context = WhitespaceContext()
        while context.running:
            instruction = program[context.pc]
            new_pc = instruction.execute(context)
            if new_pc:
                raise NotImplementedError("jumping around")
            else:
                context.pc += 1
