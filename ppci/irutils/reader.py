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
            ("OTHER", r"[\.,=:;\-\?+*\[\]/\(\)]|>|<|{|}|&|\^|\|"),
        ]
        tok_re = "|".join("(?P<%s>%s)" % pair for pair in tok_spec)
        gettok = re.compile(tok_re).match
        keywords = [
            "global",
            "local",
            "function",
            "module",
            "procedure",
            "store",
            "load",
            "cast",
            "jmp",
            "cjmp",
            "exit",
            "return",
        ]

        def tokenize():
            for line in lines:
                if not line:
                    continue  # Skip empty lines
                mo = gettok(line)
                while mo:
                    typ = mo.lastgroup
                    val = mo.group(typ)
                    if typ == "ID":
                        if val in keywords:
                            typ = val
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

        try:
            module = self.parse_module()
            return module
        except IrParseException as e:
            print(e)
            raise Exception(str(e))

    def next_token(self):
        t = self.token
        if t[0] != "eof":
            self.token = self.tokens.__next__()
        return t

    @property
    def peak(self):
        return self.token[0]

    def consume(self, typ):
        if self.peak == typ:
            return self.next_token()
        else:
            raise IrParseException(
                'Expected "{}" got "{}"'.format(typ, self.peak)
            )

    def parse_module(self):
        """ Entry for recursive descent parser """
        self.consume("module")
        name = self.consume("ID")[1]
        module = ir.Module(name)
        self.consume(";")
        while self.peak != "eof":
            if self.peak == "local":
                self.consume("local")
                binding = ir.Binding.LOCAL
            else:
                self.consume("global")
                binding = ir.Binding.GLOBAL

            if self.peak in ["function", "procedure"]:
                module.add_function(self.parse_function(binding))
            else:
                raise IrParseException(
                    "Expected function got {}".format(self.peak)
                )
        return module

    def parse_function(self, binding):
        """ Parse a function or procedure """
        if self.peak == "function":
            self.consume("function")
            return_type = self.parse_type()
            name = self.consume("ID")[1]
            function = ir.Function(name, binding, return_type)
        else:
            self.consume("procedure")
            name = self.consume("ID")[1]
            function = ir.Procedure(name, binding)

        # Setup maps:
        self.val_map = {}
        self.block_map = {}

        self.consume("(")
        while self.peak != ")":
            ty = self.parse_type()
            name = self.consume("ID")[1]
            param = ir.Parameter(name, ty)
            function.add_parameter(param)
            self.define_value(param)
            if self.peak != ",":
                break
            else:
                self.consume(",")
        self.consume(")")
        self.consume("{")
        while self.peak != "}":
            block = self.parse_block(function)
            self.block_map[block.name] = block
        self.consume("}")

        return function

    def parse_type(self):
        """ Parse a single type """
        type_map = {t.name: t for t in ir.all_types}
        type_name = self.consume("ID")[1]
        return type_map[type_name]

    def _get_block(self, name):
        """ Get or create the given block """
        if name not in self.block_map:
            self.block_map[name] = ir.Block(name)
        return self.block_map[name]

    def parse_block(self, function):
        """ Read a single block from file """
        name = self.consume("ID")[1]
        block = self._get_block(name)
        function.add_block(block)
        if function.entry is None:
            function.entry = block
        self.consume(":")
        self.consume("{")
        while self.peak != "}":
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
        name = self.consume("ID")[1]
        self.consume("=")
        if self.peak == "ID":
            a = self.consume("ID")[1]
            if a == "phi":
                ins = ir.Phi(name, ty)
                b1 = self._get_block(self.consume("ID")[1])
                self.consume(":")
                v1 = self.find_val(self.consume("ID")[1])
                ins.set_incoming(b1, v1)
                while self.peak == ",":
                    self.consume(",")
                    b1 = self._get_block(self.consume("ID")[1])
                    self.consume(":")
                    v1 = self.find_val(self.consume("ID")[1])
                    ins.set_incoming(b1, v1)
            else:
                if self.peak in ["+", "-"]:
                    # Go for binop
                    op = self.consume(self.peak)[1]
                    b = self.consume("ID")[1]
                    a = self.find_val(a)
                    b = self.find_val(b)
                    ins = ir.Binop(a, op, b, name, ty)
                else:
                    raise NotImplementedError(self.peak)
        elif self.peak == "NUMBER":
            cn = self.consume("NUMBER")[1]
            ins = ir.Const(cn, name, ty)
        else:  # pragma: no cover
            raise NotImplementedError(self.peak)
        return ins

    def parse_cjmp(self):
        self.consume("cjmp")
        a = self.consume("ID")[1]
        op = self.consume(self.peak)[0]
        b = self.consume("ID")[1]
        self.consume("?")
        L1 = self.consume("ID")[1]
        L1 = self._get_block(L1)
        self.consume(":")
        L2 = self.consume("ID")[1]
        L2 = self._get_block(L2)
        a = self.find_val(a)
        b = self.find_val(b)
        ins = ir.CJump(a, op, b, L1, L2)
        return ins

    def parse_jmp(self):
        self.consume("jmp")
        L1 = self.consume("ID")[1]
        L1 = self._get_block(L1)
        ins = ir.Jump(L1)
        return ins

    def parse_return(self):
        self.consume("return")
        v = self.find_val(self.consume("ID")[1])
        ins = ir.Return(v)
        return ins

    def parse_statement(self):
        """ Parse a single instruction line """
        if self.peak == "jmp":
            ins = self.parse_jmp()
        elif self.peak == "cjmp":
            ins = self.parse_cjmp()
        elif self.peak == "return":
            ins = self.parse_return()
        elif self.peak == "store":
            raise Exception()
        elif self.peak == "exit":
            self.consume("exit")
            ins = ir.Exit()
        else:
            ins = self.parse_assignment()
            self.define_value(ins)
        self.consume(";")
        return ins
