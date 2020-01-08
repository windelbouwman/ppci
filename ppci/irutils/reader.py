""" Parsing IR-code from a test form.
"""

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


class Reader:
    """ Read IR-code from file """

    def __init__(self):
        pass

    def read(self, f) -> ir.Module:
        """ Read ir code from file f """
        # Read lines from the file:
        lines = [line.rstrip() for line in f]

        # Create a regular expression for the lexing part:
        tok_spec = [
            ("NUMBER", r"\d+"),
            ("ID", r"[A-Za-z][A-Za-z\d_]*"),
            ("SKIP", r"\s+"),
            (
                "OTHER",
                r"[\.,:;\-\?\+*\[\]/\(\)]|!=|==|<=|>=|>|<|=|{|}|&|\^|\|",
            ),
        ]
        tok_re = "|".join("(?P<%s>%s)" % pair for pair in tok_spec)
        gettok = re.compile(tok_re).match
        keywords = [
            "module",
            "external",
            "global",
            "local",
            "variable",
            "function",
            "procedure",
        ]

        instructions = [
            "store",
            "load",
            "cast",
            "jmp",
            "cjmp",
            "exit",
            "return",
        ]

        keywords += instructions

        def tokenize():
            for line in lines:
                if not line:
                    continue  # Skip empty lines
                mo = gettok(line)
                while mo:
                    typ = mo.lastgroup
                    val = mo.group(typ)
                    if typ == "ID":
                        # if val in keywords:
                        # typ = val
                        yield (typ, val)
                    elif typ == "OTHER":
                        typ = val
                        yield (typ, val)
                    elif typ == "SKIP":
                        pass
                    elif typ == "NUMBER":
                        yield (typ, int(val))
                    else:
                        raise NotImplementedError(str(typ))
                    pos = mo.end()
                    mo = gettok(line, pos)
                if len(line) != pos:
                    raise IrParseException("Lex fault")
            yield ("eof", "eof")

        self.tokens = tokenize()
        self.token = self.tokens.__next__()

        module = self.parse_module()
        return module

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
            raise IrParseException(
                'Expected "{}" got "{}"'.format(typ, self.peek)
            )

    def at_keyword(self, keyword):
        """ Test if we are at some keyword. """
        return self.token == ("ID", keyword)

    def consume_keyword(self, keyword):
        val = self.consume("ID")[1]
        if val != keyword:
            raise IrParseException(
                'Expected "{}" got "{}"'.format(keyword, val)
            )

    def parse_module(self):
        """ Entry for recursive descent parser """
        self.consume_keyword("module")
        name = self.consume("ID")[1]
        module = ir.Module(name)
        self.consume(";")
        while self.peek != "eof":
            if self.at_keyword("external"):
                self.parse_external(module)
            else:
                self.parse_declaration(module)

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

        if self.at_keyword("function") or self.at_keyword("procedure"):
            module.add_function(self.parse_function(binding))
        else:
            raise IrParseException(
                "Expected function got {}".format(self.peek)
            )

    def parse_function(self, binding):
        """ Parse a function or procedure """
        if self.at_keyword("function"):
            self.consume_keyword("function")
            return_type = self.parse_type()
            name = self.parse_id()
            function = ir.Function(name, binding, return_type)
        else:
            self.consume_keyword("procedure")
            name = self.parse_id()
            function = ir.Procedure(name, binding)

        # Setup maps:
        self.val_map = {}
        self.block_map = {}

        self.consume("(")
        while self.peek != ")":
            ty = self.parse_type()
            name = self.parse_id()
            param = ir.Parameter(name, ty)
            function.add_parameter(param)
            self.define_value(param)
            if self.peek != ",":
                break
            else:
                self.consume(",")
        self.consume(")")
        self.consume("{")
        while self.peek != "}":
            block = self.parse_block(function)
            self.block_map[block.name] = block
        self.consume("}")

        return function

    def parse_type(self):
        """ Parse a single type """
        if self.at_keyword("blob"):
            self.consume_keyword("blob")
            self.consume("<")
            size = self.consume("NUMBER")[1]
            self.consume(":")
            alignment = self.consume("NUMBER")[1]
            self.consume(">")
            typ = ir.BlobDataTyp(size, alignment)
        else:
            type_map = {t.name: t for t in ir.all_types}
            type_name = self.parse_id()
            typ = type_map[type_name]
        return typ

    def _get_block(self, name):
        """ Get or create the given block """
        if name not in self.block_map:
            self.block_map[name] = ir.Block(name)
        return self.block_map[name]

    def parse_block(self, function):
        """ Read a single block from file """
        name = self.parse_id()
        block = self._get_block(name)
        function.add_block(block)
        if function.entry is None:
            function.entry = block
        self.consume(":")
        self.consume("{")
        while self.peek != "}":
            ins = self.parse_statement()
            block.add_instruction(ins)
        self.consume("}")
        return block

    def define_value(self, v):
        """ Define a value """
        if v.name in self.val_map:
            # Now what? Double declaration?
            old_value = self.val_map[v.name]
            assert isinstance(old_value, ir.Undefined)
            old_value.replace_by(v)
        self.val_map[v.name] = v

    def find_val(self, name, ty=ir.i32):
        if name not in self.val_map:
            self.val_map[name] = ir.Undefined(name, ty)
        return self.val_map[name]

    def find_block(self, name):
        return self.block_map[name]

    def parse_assignment(self):
        """ Parse an instruction with shape 'ty' 'name' '=' ... """
        ty = self.parse_type()
        name = self.parse_id()
        self.consume("=")
        if self.peek == "ID":
            a = self.consume("ID")[1]
            if a == "phi":
                ins = ir.Phi(name, ty)
                b1 = self._get_block(self.parse_id())
                self.consume(":")
                v1 = self.find_val(self.parse_id())
                ins.set_incoming(b1, v1)
                while self.peek == ",":
                    self.consume(",")
                    b1 = self._get_block(self.parse_id())
                    self.consume(":")
                    v1 = self.find_val(self.parse_id())
                    ins.set_incoming(b1, v1)
            elif a == "alloc":
                size = self.parse_integer()
                self.consume_keyword("bytes")
                self.consume_keyword("aligned")
                self.consume_keyword("at")
                alignment = self.parse_integer()
                ins = ir.Alloc(name, size, alignment)
            elif a == "load":
                address = self.parse_ref()
                ins = ir.Load(address, name, ty)
            elif a == "cast":
                value = self.parse_ref()
                ins = ir.Cast(value, name, ty)
            elif a == "call":
                ins = ir.FunctionCall()
            else:
                if self.peek in ["+", "-"]:
                    # Go for binop
                    op = self.consume(self.peek)[1]
                    b = self.parse_id()
                    a = self.find_val(a)
                    b = self.find_val(b)
                    ins = ir.Binop(a, op, b, name, ty)
                else:
                    raise NotImplementedError(self.peek)
        elif self.peek == "NUMBER":
            cn = self.consume("NUMBER")[1]
            ins = ir.Const(cn, name, ty)
        elif self.peek == "&":
            self.consume("&")
            src = self.find_val(self.parse_id(), ty=ir.BlobDataTyp(1, 1))
            assert ty is ir.ptr
            ins = ir.AddressOf(src, name)
        else:  # pragma: no cover
            raise NotImplementedError(self.peek)
        return ins

    def parse_integer(self):
        return self.consume("NUMBER")[1]

    def parse_id(self):
        return self.consume("ID")[1]

    def parse_ref(self):
        """ Parse a reference to another variable. """
        return self.find_val(self.parse_id())

    def parse_cjmp(self):
        self.consume_keyword("cjmp")
        a = self.parse_ref()
        op = self.consume(self.peek)[0]
        b = self.parse_ref()
        self.consume("?")
        L1 = self.parse_id()
        L1 = self._get_block(L1)
        self.consume(":")
        L2 = self.parse_id()
        L2 = self._get_block(L2)
        ins = ir.CJump(a, op, b, L1, L2)
        return ins

    def parse_jmp(self):
        self.consume_keyword("jmp")
        L1 = self.parse_id()
        L1 = self._get_block(L1)
        ins = ir.Jump(L1)
        return ins

    def parse_return(self):
        self.consume_keyword("return")
        v = self.find_val(self.parse_id())
        ins = ir.Return(v)
        return ins

    def parse_function_arguments(self):
        self.consume("(")
        arguments = []
        if self.peek != ")":
            argument = self.parse_ref()
            arguments.append(argument)
            while self.peek == ",":
                self.consume(",")
                argument = self.parse_ref()
                arguments.append(argument)
        self.consume(")")
        return arguments

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
            value = self.parse_ref()
            self.consume(",")
            address = self.parse_ref()
            ins = ir.Store(value, address)
        elif self.at_keyword("exit"):
            self.consume_keyword("exit")
            ins = ir.Exit()
        elif self.at_keyword("call"):
            self.consume_keyword("call")
            callee = self.parse_ref()
            # callee = name
            arguments = self.parse_function_arguments()
            ins = ir.ProcedureCall(callee, arguments)
        else:
            ins = self.parse_assignment()
            self.define_value(ins)
        self.consume(";")
        return ins
