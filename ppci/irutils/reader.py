""" Parsing IR-code from a textual form.
"""

from binascii import unhexlify
import re
from .. import ir


def read_module(f) -> ir.Module:
    """ Read an ir-module from file.

    Args:
        f: A file like object ready to be read in text modus.

    Returns:
        The loaded ir-module.
    """
    return Reader().read(f)


class IrParseException(Exception):
    """ Exception raised when reading of IR-code fails.
    """

    pass


def tokenize(lines):
    # Create a regular expression for the lexing part:
    tok_spec = [
        ("FLOAT", r"\-?\d+\.\d+"),
        ("INT", r"\-?\d+"),
        ("STRING", r"'[^']*'"),
        ("ID", r"[A-Za-z][A-Za-z\d_]*"),
        ("SKIP", r"\s+"),
        (
            "OTHER",
            r"[,:;\-\?\+*%\[\]/\(\)]|<<|>>|!=|==|<=|>=|>|<|=|{|}|&|\^|\|",
        ),
    ]
    tok_re = "|".join("(?P<%s>%s)" % pair for pair in tok_spec)
    gettok = re.compile(tok_re).match
    for row, line in enumerate(lines, 1):
        if not line:
            continue  # Skip empty lines
        mo = gettok(line)
        pos = 0
        while mo:
            typ = mo.lastgroup
            val = mo.group(typ)
            if typ == "ID":
                yield (typ, val, row, pos)
            elif typ == "OTHER":
                typ = val
                yield (typ, val, row, pos)
            elif typ == "SKIP":
                pass
            elif typ == "INT":
                yield (typ, int(val), row, pos)
            elif typ == "FLOAT":
                yield (typ, float(val), row, pos)
            elif typ == "STRING":
                yield (typ, val[1:-1], row, pos)
            else:
                raise NotImplementedError(str(typ))
            pos = mo.end()
            mo = gettok(line, pos)
        if len(line) != pos:
            raise IrParseException(
                "Lex fault at row {}, column {}".format(row, pos)
            )
    yield ("eof", "eof", 0, 0)


class Scope:
    def __init__(self):
        self.block_map = {}
        self.value_map = {}


class Reader:
    """ Read IR-code from file """

    def __init__(self):
        self.undefined_values = {}
        self.scopes = []

    def read(self, f) -> ir.Module:
        """ Read ir code from file f """
        self.prepare_lexing(f)
        module = self.parse_module()
        return module

    def prepare_lexing(self, f):
        # Read lines from the file:
        lines = [line.rstrip() for line in f]
        self.tokens = tokenize(lines)
        self.token = self.tokens.__next__()

    # Lexical helpers:
    def next_token(self):
        t = self.token
        if t[0] != "eof":
            self.token = self.tokens.__next__()
        return t

    @property
    def peek(self):
        return self.token[0]

    def consume(self, typ):
        if self.peek == typ:
            return self.next_token()
        else:
            self.error('Expected "{}" got "{}"'.format(typ, self.peek))

    def error(self, msg):
        """ Something went wrong. """
        row = self.token[2]
        column = self.token[3]
        raise IrParseException(
            msg + " at row {}, column {}".format(row, column)
        )

    def at_keyword(self, keyword):
        """ Test if we are at some keyword. """
        return self.token[0] == "ID" and self.token[1] == keyword

    def consume_keyword(self, keyword):
        """ Consume a specific identifier. """
        val = self.parse_id()
        if val != keyword:
            self.error('Expected "{}" got "{}"'.format(keyword, val))

    # Top level contraptions:

    def parse_module(self):
        """ Entry for recursive descent parser """
        self.consume_keyword("module")
        name = self.parse_id()
        module = ir.Module(name)
        self.consume(";")

        self.enter_scope()
        while self.peek != "eof":
            if self.at_keyword("external"):
                self.parse_external(module)
            else:
                self.parse_declaration(module)
        self.leave_scope()

        return module

    def parse_external(self, module):
        """ Parse external variable. """
        self.consume_keyword("external")
        if self.at_keyword("function"):
            self.consume_keyword("function")
            return_type = self.parse_type()
            name = self.parse_id()
            argument_types = self.parse_braced_types()
            external = ir.ExternalFunction(name, argument_types, return_type)
        elif self.at_keyword("procedure"):
            self.consume_keyword("procedure")
            name = self.parse_id()
            argument_types = self.parse_braced_types()
            external = ir.ExternalProcedure(name, argument_types)
        elif self.at_keyword("variable"):
            self.consume_keyword("variable")
            name = self.parse_id()
            external = ir.ExternalVariable(name)
        else:
            raise NotImplementedError(str(self.peek))
        self.consume(";")
        self.define_value(external)
        module.add_external(external)

    def parse_braced_types(self):
        argument_types = []
        self.consume("(")
        if self.peek != ")":
            argument_type = self.parse_type()
            argument_types.append(argument_type)
            while self.peek == ",":
                self.consume(",")
                argument_type = self.parse_type()
                argument_types.append(argument_type)
        self.consume(")")
        return argument_types

    def parse_declaration(self, module):
        if self.at_keyword("local"):
            self.consume_keyword("local")
            binding = ir.Binding.LOCAL
        else:
            self.consume_keyword("global")
            binding = ir.Binding.GLOBAL

        if self.at_keyword("variable"):
            module.add_variable(self.parse_variable(binding))
        elif self.at_keyword("function") or self.at_keyword("procedure"):
            module.add_function(self.parse_function(binding))
        else:
            self.error("Expected function got {}".format(self.peek))

    def parse_variable(self, binding):
        self.consume_keyword("variable")
        name = self.parse_id()
        self.consume("(")
        amount = self.parse_integer()
        self.consume_keyword("bytes")
        self.consume_keyword("aligned")
        self.consume_keyword("at")
        alignment = self.parse_integer()
        self.consume(")")
        variable = ir.Variable(name, binding, amount, alignment)
        self.define_value(variable)
        return variable

    def parse_function(self, binding):
        """ Parse a function or procedure """
        if self.at_keyword("function"):
            self.consume_keyword("function")
            return_type = self.parse_type()
            name = self.parse_id()
            subroutine = ir.Function(name, binding, return_type)
        else:
            self.consume_keyword("procedure")
            name = self.parse_id()
            subroutine = ir.Procedure(name, binding)

        self.define_value(subroutine)

        self.enter_scope()

        self.consume("(")
        while self.peek != ")":
            ty = self.parse_type()
            name = self.parse_id()
            param = ir.Parameter(name, ty)
            subroutine.add_parameter(param)
            self.define_value(param)
            if self.peek != ",":
                break
            else:
                self.consume(",")
        self.consume(")")
        self.consume("{")
        while self.peek != "}":
            block = self.parse_block(subroutine)
            if subroutine.entry is None:
                subroutine.entry = block

        self.consume("}")
        self.leave_scope()

        return subroutine

    def parse_type(self):
        """ Parse a single type """
        if self.at_keyword("blob"):
            self.consume_keyword("blob")
            self.consume("<")
            size = self.parse_integer()
            self.consume(":")
            alignment = self.parse_integer()
            self.consume(">")
            typ = ir.BlobDataTyp(size, alignment)
        else:
            type_map = {t.name: t for t in ir.all_types}
            type_name = self.parse_id()
            typ = type_map[type_name]
        return typ

    def parse_block(self, function):
        """ Read a single block from file """
        name = self.parse_id()
        block = self._get_block(name)
        assert block.function is None
        function.add_block(block)
        self.consume(":")
        self.consume("{")
        while self.peek != "}":
            ins = self.parse_statement()
            block.add_instruction(ins)
        self.consume("}")
        return block

    def enter_scope(self):
        self.scopes.append(Scope())

    def leave_scope(self):
        self.scopes.pop()

    def define_value(self, value):
        """ Define a value """
        if value.name in self.undefined_values:
            # Now what? Double declaration?
            old_value = self.undefined_values.pop(value.name)
            assert isinstance(old_value, ir.Undefined)
            old_value.replace_by(value)
        self.scopes[-1].value_map[value.name] = value

    def find_value(self, name, ty=ir.i32):
        """ Try hard to find a value.

        If the value is undefined, create a placeholder undefined
        value.
        """
        for scope in reversed(self.scopes):
            if name in scope.value_map:
                value = scope.value_map[name]
                break
        else:
            if name in self.undefined_values:
                value = self.undefined_values[name]
            else:
                value = ir.Undefined(name, ty)
                self.undefined_values[name] = value
        return value

    def _get_block(self, name):
        """ Get or create the given block """
        scope = self.scopes[-1]
        if name in scope.block_map:
            block = scope.block_map[name]
        else:
            block = ir.Block(name)
            scope.block_map[name] = block
        return block

    def parse_assignment(self):
        """ Parse an instruction with shape 'ty' 'name' '=' ... """
        ty = self.parse_type()
        name = self.parse_id()
        self.consume("=")
        if self.peek == "ID":
            a = self.parse_id()
            if self.peek in ir.Binop.ops:
                # Go for binop
                op = self.consume(self.peek)[1]
                b = self.parse_id()
                a = self.find_value(a)
                b = self.find_value(b)
                ins = ir.Binop(a, op, b, name, ty)
            elif a == "phi":
                ins = ir.Phi(name, ty)
                b1 = self.parse_block_ref()
                self.consume(":")
                v1 = self.parse_value_ref(ty=ty)
                ins.set_incoming(b1, v1)
                while self.peek == ",":
                    self.consume(",")
                    b1 = self.parse_block_ref()
                    self.consume(":")
                    v1 = self.parse_value_ref(ty=ty)
                    ins.set_incoming(b1, v1)
            elif a == "alloc":
                size = self.parse_integer()
                self.consume_keyword("bytes")
                self.consume_keyword("aligned")
                self.consume_keyword("at")
                alignment = self.parse_integer()
                ins = ir.Alloc(name, size, alignment)
            elif a == "load":
                address = self.parse_value_ref()
                ins = ir.Load(address, name, ty)
            elif a == "cast":
                value = self.parse_value_ref()
                ins = ir.Cast(value, name, ty)
            elif a == "call":
                callee = self.parse_value_ref()
                arguments = self.parse_function_arguments()
                ins = ir.FunctionCall(callee, arguments, name, ty)
            elif a == "literal":
                data = self.consume("STRING")[1]
                data = unhexlify(data)
                ins = ir.LiteralData(data, name)
            else:
                raise NotImplementedError(a)
        elif self.peek in ["INT", "FLOAT"]:
            cn = self.parse_number()
            ins = ir.Const(cn, name, ty)
        elif self.peek == "&":
            self.consume("&")
            src = self.parse_value_ref(ty=ir.BlobDataTyp(1, 1))
            assert ty is ir.ptr
            ins = ir.AddressOf(src, name)
        elif self.peek == "-":
            self.consume("-")
            operation = "-"
            a = self.parse_value_ref()
            ins = ir.Unop(operation, a, name, ty)
        else:  # pragma: no cover
            raise NotImplementedError(self.peek)
        return ins

    def parse_integer(self):
        return self.consume("INT")[1]

    def parse_number(self):
        if self.peek == "INT":
            return self.consume("INT")[1]
        elif self.peek == "FLOAT":
            return self.consume("FLOAT")[1]
        else:
            self.error("Expected int or float.")

    def parse_id(self):
        return self.consume("ID")[1]

    def parse_value_ref(self, ty=ir.ptr):
        """ Parse a reference to another variable. """
        return self.find_value(self.parse_id(), ty=ty)

    def parse_block_ref(self):
        return self._get_block(self.parse_id())

    def parse_statement(self):
        """ Parse a single instruction line """
        if self.at_keyword("jmp"):
            ins = self.parse_jmp()
        elif self.at_keyword("cjmp"):
            ins = self.parse_cjmp()
        elif self.at_keyword("return"):
            ins = self.parse_return()
        elif self.at_keyword("store"):
            self.consume_keyword("store")
            value = self.parse_value_ref()
            self.consume(",")
            address = self.parse_value_ref()
            ins = ir.Store(value, address)
        elif self.at_keyword("exit"):
            self.consume_keyword("exit")
            ins = ir.Exit()
        elif self.at_keyword("call"):
            self.consume_keyword("call")
            callee = self.parse_value_ref()
            arguments = self.parse_function_arguments()
            ins = ir.ProcedureCall(callee, arguments)
        else:
            ins = self.parse_assignment()
            self.define_value(ins)
        self.consume(";")
        return ins

    def parse_cjmp(self):
        self.consume_keyword("cjmp")
        a = self.parse_value_ref()
        op = self.consume(self.peek)[0]
        b = self.parse_value_ref()
        self.consume("?")
        L1 = self.parse_block_ref()
        self.consume(":")
        L2 = self.parse_block_ref()
        ins = ir.CJump(a, op, b, L1, L2)
        return ins

    def parse_jmp(self):
        self.consume_keyword("jmp")
        L1 = self.parse_block_ref()
        ins = ir.Jump(L1)
        return ins

    def parse_return(self):
        self.consume_keyword("return")
        v = self.parse_value_ref()
        ins = ir.Return(v)
        return ins

    def parse_function_arguments(self):
        self.consume("(")
        arguments = []
        if self.peek != ")":
            argument = self.parse_value_ref()
            arguments.append(argument)
            while self.peek == ",":
                self.consume(",")
                argument = self.parse_value_ref()
                arguments.append(argument)
        self.consume(")")
        return arguments
