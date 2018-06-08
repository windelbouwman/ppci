"""

2nd attempt to parse WAT (wasm text) as parsed s-expressions.

More or less a python version of this code:
https://github.com/WebAssembly/wabt/blob/master/src/wast-parser.cc
"""

from collections import defaultdict
import enum
from ..lang.sexpr import parse_sexpr
from .opcodes import OPERANDS, OPCODES
from .util import datastring2bytes
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
        self.definitions = defaultdict(list)

    def load_module(self, t):
        """ Load a module from a tuple """
        self._feed(t)

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
            elif kind == 'data':
                self.load_data()
            elif kind == 'elem':
                self.load_elem()
            elif kind == 'export':
                self.load_export()
            elif kind == 'func':
                self.load_func()
            elif kind == 'global':
                self.load_global()
            elif kind == 'import':
                self.load_import()
            elif kind == 'memory':
                self.load_memory()
            elif kind == 'start':
                self.load_start()
            elif kind == 'table':
                self.load_table()
            else:
                raise NotImplementedError(kind)

        if top_module_tag:
            self._expect(Token.RPAR)

        self._expect(Token.EOF)

        # Take all definitions by section id order:
        definitions = []
        for name in components.SECTION_IDS:
            for definition in self.definitions[name]:
                definitions.append(definition)
        self.module.definitions = definitions
        print(definitions)

    def add_definition(self, definition):
        print(definition.to_string())
        self.definitions[definition.__name__].append(definition)

    def gen_id(self, kind):
        return '${}'.format(len(self.definitions[kind]))

    # Section types:
    def load_type(self):
        """ Load a tuple starting with 'type' """
        id = self._parse_optional_id(default='$0')
        self._expect(Token.LPAR, 'func')
        params, results = self._parse_function_signature()
        self._expect(Token.RPAR, Token.RPAR)
        self.add_definition(components.Type(id, params, results))

    def _parse_optional_id(self, default=None):
        if self._at_id():
            id = self._take()
        else:
            id = default
        return id

    def _parse_type_use(self):
        if self._match(Token.LPAR, 'type'):
            self._expect(Token.LPAR, 'type')
            ref = self._parse_var()
            self._expect(Token.RPAR)
        elif self._match(Token.LPAR, 'param') or self._match(Token.LPAR, 'result'):
            params, results = self._parse_function_signature()
            ref = self.gen_id('type')
            self.add_definition(
                components.Type(ref, params, results))
        else:
            ref = self.gen_id('type')
            self.add_definition(
                components.Type(ref, [], []))
        return ref

    def _parse_function_signature(self):
        params = self._parse_param_list()
        results = self._parse_result_list()
        return params, results

    def _parse_param_list(self):
        return self._parse_type_bound_value_list('param')

    def _parse_type_bound_value_list(self, kind):
        """ Parse thing like (locals i32) (locals $foo i32) """
        params = []
        while self._match(Token.LPAR, kind):
            self._expect(Token.LPAR, kind)
            if self._match(Token.RPAR):  # (param,)
                self._expect(Token.RPAR)
            else:
                if self._at_id():  # (param $id i32)
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
                if id:
                    ref = id
                else:
                    ref = 1  # TODO: figure out ref
                    raise NotImplementedError('generate implicit id')
                self.add_definition(
                    components.Type(ref, params, results))
            else:
                self._expect(Token.LPAR, 'func')
                params, results = self._parse_function_signature()
                # Insert type:
                ref = 1  # TODO: figure out ref
                self.add_definition(
                    components.Type(ref, params, results))
                self._expect(Token.RPAR)
            info = (ref,)
        elif kind == 'table':
            id = self._parse_optional_id()
            min = self._take()
            max = None
            table_kind = self._take()
            assert table_kind == 'anyfunc'
            info = (table_kind, min, max)
        elif kind == 'memory':
            id = self._parse_optional_id()
            min = self._take()
            if self._match(Token.RPAR):
                max = None
            else:
                max = self._take()
            info = (min, max)
        elif kind == 'global':
            id = self._parse_optional_id()
            typ = self._take()
            mutable = False  # TODO?
            info = (typ, mutable)
        else:  # pragma: no cover
            raise NotImplementedError(kind)

        self._expect(Token.RPAR)
        self._expect(Token.RPAR)
        self.add_definition(
            components.Import(modname, name, kind, id, info))

    def load_export(self):
        """ Parse a toplevel export """
        name = self._take()
        self._expect(Token.LPAR)
        kind = self._take()
        ref = self._parse_var()
        self._expect(Token.RPAR)
        self._expect(Token.RPAR)
        self.add_definition(
            components.Export(name, kind, ref))

    def load_start(self):
        """ Parse a toplevel start """
        name = self._parse_var()
        self._expect(Token.RPAR)
        self.add_definition(components.Start(name))

    def load_table(self):
        """ Parse a table """
        id = self._parse_optional_id()
        self._parse_inline_export('table', id)
        if self._match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            min = self._take()
            if self._match('anyfunc'):
                max = None
            else:
                max = self._take()
            kind = self._take()
            self._expect(Token.RPAR)
            info = (kind, min, max)
            self.add_definition(
                components.Import(modname, name, 'table', id, info))
        else:
            min = self._take()
            max = None
            kind = self._take()
            self._expect(Token.RPAR)
            self.add_definition(
                components.Table(id, kind, min, max))

    def load_elem(self):
        raise NotImplementedError()
        self._expect(Token.RPAR)

    def load_memory(self):
        """ Load a memory definition """
        id = self._parse_optional_id(default=self.gen_id('memory'))
        self._parse_inline_export('memory', id)
        if self._match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            min = self._take()
            if self._match(Token.RPAR):
                max = None
            else:
                max = self._take()
            self._expect(Token.RPAR)
            info = (min, max)
            self.add_definition(
                components.Import(modname, name, 'memory', id, info))
        else:
            min = self._take()
            if self._match(Token.RPAR):
                max = None
            else:
                max = self._take()
            self._expect(Token.RPAR)
            self.add_definition(
                components.Memory(id, min, max))

    def load_global(self):
        """ Load a global definition """
        id = self._parse_optional_id()
        self._parse_inline_export('global', id)
        if self._match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            typ = self._take()
            mutable = False  # TODO?
            self._expect(Token.RPAR)
            info = (typ, mutable)
            self.add_definition(
                components.Import(modname, name, 'global', id, info))
        else:
            typ = self._take()
            mutable = False
            init = self._load_instruction_list()[0]
            self._expect(Token.RPAR)
            self.add_definition(
                components.Global(id, typ, mutable, init))

    def load_data(self):
        """ Load data """
        ref = 0
        offset = self._load_instruction_list()[0]
        data = bytearray()
        while not self._match(Token.RPAR):
            txt = self._take()
            assert isinstance(txt, str)
            data.extend(datastring2bytes(txt))
        data = bytes(data)

        self._expect(Token.RPAR)
        self.add_definition(
            components.Data(ref, offset, data))

    def _parse_var(self):
        assert self._at_id()
        return self._take()

    def load_func(self):
        id = self._parse_optional_id(default=self.gen_id('func'))

        self._parse_inline_export('func', id)

        if self._match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            ref = self._parse_type_use()
            self._expect(Token.RPAR)
            info = (ref,)
            self.add_definition(
                components.Import(modname, name, 'func', id, info))
        else:
            ref = self._parse_type_use()
            localz = self._parse_locals()
            instructions = self._load_instruction_list()
            self._expect(Token.RPAR)
            self.add_definition(
                components.Func(id, ref, localz, instructions))

    def _parse_locals(self):
        return self._parse_type_bound_value_list('local')

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
            if self._match(Token.LPAR):
                # Nested instruction!
                l.extend(self._load_instruction())
            else:
                args.append(self._take())
        self._expect(Token.RPAR)

        i = components.Instruction(opcode, *args)
        l.append(i)
        return l

    # Inline stuff:
    def _parse_inline_import(self):
        self._expect(Token.LPAR, 'import')
        modname = self._take()
        name = self._take()
        self._expect(Token.RPAR)
        return modname, name

    def _parse_inline_export(self, kind, ref):
        while self._match(Token.LPAR, 'export'):
            self._expect(Token.LPAR, 'export')
            name = self._take()
            self._expect(Token.RPAR)
            self.add_definition(
                components.Export(name, kind, ref))

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
