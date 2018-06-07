"""

2nd attempt to parse WAT (wasm text) as parsed s-expressions.
"""

import enum
from ..lang.sexpr import parse_sexpr
from .opcodes import OPERANDS, OPCODES
from . import components


def load_tuple(module, t):
    """ Load contents of tuple t into module """
    # Parse nested strings at top level:
    t2 = []
    for e in t:
        if isinstance(e, str) and e.startswith('('):
            e = parse_sexpr(e)
        t2.append(e)
    t2 = tuple(t2)

    TupleLoader(module).load_module(t2)


class TupleLoader:
    def __init__(self, module):
        self.module = module

    def load_module(self, t):
        """ Load a module from a tuple """
        self._feed(t)
        self.module.definitions = []

        top_module_tag = self._match(Token.LPAR, 'module')
        if top_module_tag:
            self._expect(Token.LPAR, 'module')

        # Detect id:
        self.module.id = self._parse_optional_id()

        while self._match(Token.LPAR):
            self._expect(Token.LPAR)
            kind = self._take()
            if kind == 'type':
                self.load_type()
            elif kind == 'import':
                self.load_import()
            elif kind == 'start':
                self.load_start()
            elif kind == 'func':
                self.load_func()
            else:
                raise NotImplementedError(kind)

        if top_module_tag:
            self._expect(Token.RPAR)

        self._expect(Token.EOF)

    def load_type(self):
        """ Load a tuple starting with 'type' """
        id = self._parse_optional_id(default='$0')
        self._expect(Token.LPAR, 'func')
        params, results = self._parse_function_signature()
        self._expect(Token.RPAR, Token.RPAR)
        self.module.definitions.append(components.Type(id, params, results))

    def _parse_optional_id(self, default=None):
        if self._at_id():
            id = self._take()
        else:
            id = default
        return id

    def _parse_function_signature(self):
        params = self._parse_param_list()
        results = self._parse_result_list()
        return params, results

    def _parse_param_list(self):
        params = []
        while self._match(Token.LPAR, 'param'):
            self._expect(Token.LPAR, 'param')
            if self._match(Token.RPAR):
                self._expect(Token.RPAR)
                pass  # (param,)
            else:
                if self._at_id():
                    # (param $id i32)
                    params.append((self._take(), self._take()))
                    self._expect(Token.RPAR)
                else:
                    # anonymous (param i32 i32 i32)
                    while not self._match(Token.RPAR):
                        p = self._take()
                        params.append((len(params), p))
                    self._expect(Token.RPAR)
        return params

    def _parse_result_list(self):
        result = []
        while self._match(Token.LPAR, 'result'):
            self._expect(Token.LPAR, 'result')
            while not self._match(Token.RPAR):
                result.append(self._take())
            self._expect(Token.RPAR)
        return result

    def load_import(self):
        modname = self._take()
        name = self._take()
        self._expect(Token.LPAR)
        kind = self._take()
        if kind == 'func':
            id = self._parse_optional_id()
            if self._match(Token.LPAR, 'type'):
                self._expect(Token.LPAR, 'type')
                ref = self._parse_var()  # Type reference
                self._expect(Token.RPAR)
            elif self._match(Token.LPAR, 'param') or self._match(Token.LPAR, 'result'):
                params, results = self._parse_function_signature()
                ref = 1  # TODO: figure out ref
                self.module.definitions.append(
                    components.Type(ref, params, results))
            else:
                self._expect(Token.LPAR, 'func')
                params, results = self._parse_function_signature()
                # Insert type:
                ref = 1  # TODO: figure out ref
                self.module.definitions.append(
                    components.Type(ref, params, results))
                self._expect(Token.RPAR)
            info = (ref,)
        elif kind == 'table':
            raise NotImplementedError()
        elif kind == 'memory':
            raise NotImplementedError()
        elif kind == 'global':
            raise NotImplementedError()
        else:
            raise NotImplementedError(kind)

        self._expect(Token.RPAR)
        self._expect(Token.RPAR)
        self.module.definitions.append(
            components.Import(modname, name, kind, id, info))

    def load_start(self):
        name = self._parse_var()
        self._expect(Token.RPAR)
        self.module.definitions.append(components.Start(name))

    def _parse_var(self):
        assert self._at_id()
        return self._take()

    def load_func(self):
        id = self._parse_optional_id()
        # TODO Handle inline exports:
        # TODO: handle imports

        if self._match(Token.LPAR, 'type'):
            self._expect(Token.LPAR, 'type')
            ref = self._parse_var()
            self._expect(Token.RPAR)
        elif self._match(Token.LPAR, 'param') or self._match(Token.LPAR, 'result'):
            params, results = self._parse_function_signature()
            ref = 1  # TODO: figure out ref
            self.module.definitions.append(
                components.Type(ref, params, results))
        else:
            ref = 1  # TODO: figure out ref
            self.module.definitions.append(
                components.Type(ref, [], []))

        localz = []
        instructions = self._load_instruction_list()
        self._expect(Token.RPAR)
        self.module.definitions.append(
            components.Func(id, ref, localz, instructions))

    def _load_instruction_list(self):
        """ Load a list of instructions """
        l = []
        while self._match(Token.LPAR):
            l.extend(self._load_instruction())
        return l

    def _load_instruction(self):
        l = []
        self._expect(Token.LPAR)
        opcode = self._take()

        if opcode == 'call_indirect':
            raise Error
        else:
            operands = OPERANDS[opcode]

        args = []
        while not self._match(Token.RPAR):
            args.append(self._take())
        self._expect(Token.RPAR)

        i = components.Instruction(opcode, *args)
        l.append(i)
        return l

    # match helper section:
    def _feed(self, t):
        self._nxt_func = self._tuple_generator(t)
        self._nxt = []

    def _tuple_generator(self, t):
        for e in self._tuple_generator_inner(t):
            yield e
        yield Token.EOF

    def _tuple_generator_inner(self, t):
        yield Token.LPAR
        for e in t:
            if isinstance(e, tuple):
                for e2 in self._tuple_generator_inner(e):
                    yield e2
            else:
                yield e
        yield Token.RPAR

    def _lookahead(self, amount: int):
        """ Return some lookahead tokens """
        assert amount > 0
        while len(self._nxt) < amount:
            nxt = next(self._nxt_func, Token.EOF)
            self._nxt.append(nxt)
        return tuple(self._nxt[:amount])

    def _expect(self, *args):
        for arg in args:
            actual = self._take()
            if actual != arg:
                raise ValueError('Expected {} but have {}'.format(
                    arg, actual))

    def _match(self, *args):
        """ Check if the given tokens are ahead """
        peek = self._lookahead(len(args))
        if peek == args:
            return True
        else:
            return False

    def _take(self):
        if not self._nxt:
            nxt = next(self._nxt_func, Token.EOF)
            self._nxt.append(nxt)
        return self._nxt.pop(0)

    def _at_id(self):
        x = self._lookahead(1)[0]
        return x and isinstance(x, str) and x.startswith('$')


class Token(enum.Enum):
    LPAR = 1
    RPAR = 2
    EOF = 3
