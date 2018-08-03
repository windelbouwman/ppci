"""

2nd attempt to parse WAT (wasm text) as parsed s-expressions.

More or less a python version of this code:
https://github.com/WebAssembly/wabt/blob/master/src/wast-parser.cc
"""

import logging

from collections import defaultdict
from ..lang.sexpr import parse_sexpr
from .opcodes import OPERANDS, OPCODES, ArgType
from .util import datastring2bytes, make_int, make_float, is_int, PAGE_SIZE
from .tuple_parser import TupleParser, Token
from . import components


logger = logging.getLogger('wat')


def load_tuple(module, t):
    """ Load contents of tuple t into module """
    if not isinstance(t, tuple):
        raise TypeError('t must be tuple')

    loader = WatTupleLoader(module)

    if any(isinstance(e, components.Definition) for e in t):
        if not all(isinstance(e, components.Definition) for e in t):
            raise TypeError('All elements must be wasm components')

        for e in t:
            loader.add_definition(e)
        module.id = None
        module.definitions = loader.gather_definitions()
    else:
        # Parse nested strings at top level:
        t2 = []
        for e in t:
            if isinstance(e, str) and e.startswith('('):
                e = parse_sexpr(e)
            t2.append(e)
        t2 = tuple(t2)

        loader.load_module(t2)


class WatTupleLoader(TupleParser):
    def __init__(self, module):
        self.module = module
        self.definitions = defaultdict(list)
        self._type_hash = {}  # (params, results) -> ref

        self.resolve_backlog = []
        self.func_backlog = []

    def load_module(self, t):
        """ Load a module from a tuple """
        self.id_maps = {
            'type': {}, 'func': {}, 'table': {},
            'memory': {}, 'global': {},
        }
        self._feed(t)

        self.expect(Token.LPAR)
        top_module_tag = self.munch('module')
        if top_module_tag:
            # Detect id:
            self.module.id = self._parse_optional_id()
        else:
            self.module.id = None

        while self.match(Token.LPAR):
            self.expect(Token.LPAR)
            kind = self.take()
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

        self.expect(Token.RPAR)
        self.expect(Token.EOF)

        self.resolve_references()
        self.module.definitions = self.gather_definitions()

    def resolve_references(self):
        # TODO: maybe this is not needed at this point?
        # Fill imports and other objects:
        for d in self.definitions['import']:
            id_map = self.id_maps[d.kind]
            id_map[d.id] = len(id_map)

        for space in ['type', 'global', 'memory', 'table', 'func']:
            for d in self.definitions[space]:
                self.id_maps[space][d.id] = len(self.id_maps[space])

        # resolve any unresolved items:
        for item in self.resolve_backlog:
            item.index = item.resolve(self.id_maps)

        # Resolve inside functions:
        assert len(self.func_backlog) == len(self.definitions['func'])
        for bl, func in zip(self.func_backlog, self.definitions['func']):
            # Fill map with local id's:
            type_idx = func.ref.resolve(self.id_maps)
            func_type = self.definitions['type'][type_idx]
            # print(func_type)
            self.id_maps['local'] = dict(
                (param[0], i)
                for i, param in
                enumerate(func_type.params))
            for i, lokal in enumerate(
                    func.locals, start=len(func_type.params)):
                if is_dollar(lokal[0]):
                    self.id_maps['local'][lokal[0]] = i

            for item in bl:
                item.index = item.resolve(self.id_maps)

    def gather_definitions(self):
        """ Take all definitions by section id order: """
        definitions = []
        for name in components.SECTION_IDS:
            for definition in self.definitions[name]:
                definitions.append(definition)
        # print(definitions)
        return definitions

    def add_definition(self, definition):
        # print(definition.to_string())
        logger.debug('Parsed %s', definition)
        space = definition.__name__
        self.definitions[space].append(definition)

    def gen_id(self, kind):
        return '${}'.format(len(self.definitions[kind]))

    # Section types:
    def load_type(self):
        """ Load a tuple starting with 'type' """
        id = self._parse_optional_id(default=self.gen_id('type'))
        self.expect(Token.LPAR, 'func')
        params, results = self._parse_function_signature()
        self.expect(Token.RPAR, Token.RPAR)
        # Note cannot reuse type here unless we remap the id whereever it is used
        self.add_definition(components.Type(id, params, results))

    def _parse_optional_id(self, default=None):
        if self._at_id():
            id = self.take()
        else:
            id = default
        return id

    def _parse_optional_ref(self, space, default=None):
        """ Parse an optional reference, defaulting to 0 """
        if self._at_ref():
            value = self.take()
        else:
            value = default

        value = self._make_ref(space, value)
        return value

    def _parse_ref(self, space):
        """ Parse a reference (int or $ref) """
        assert self._at_ref()
        value = self.take()
        return self._make_ref(space, value)

    def _add_or_reuse_type_definition(self, params, results):
        key = tuple(params), tuple(results)
        ref = self._type_hash.get(key, None)
        if ref is None:
            type_id = self.gen_id('type')
            self.add_definition(
                components.Type(type_id, params, results))
            ref = self._make_ref('type', type_id)
            self._type_hash[key] = ref
        return ref

    def _parse_type_use(self):
        if self.match(Token.LPAR, 'type'):
            self.expect(Token.LPAR, 'type')
            ref = self._parse_ref('type')
            self.expect(Token.RPAR)
        elif self.match(Token.LPAR, 'param') or \
                self.match(Token.LPAR, 'result'):
            params, results = self._parse_function_signature()
            ref = self._add_or_reuse_type_definition(params, results)
        else:
            ref = self._add_or_reuse_type_definition([], [])
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
        while self.munch(Token.LPAR, kind):
            if self.match(Token.RPAR):  # (param,)
                self.expect(Token.RPAR)
            else:
                if self._at_id():  # (param $id i32)
                    params.append((self.take(), self.take()))
                    self.expect(Token.RPAR)
                else:
                    # anonymous (param i32 i32 i32)
                    while not self.match(Token.RPAR):
                        p = self.take()
                        params.append((len(params), p))
                    self.expect(Token.RPAR)
        return params

    def _parse_result_list(self):
        result = []
        while self.munch(Token.LPAR, 'result'):
            while not self.match(Token.RPAR):
                result.append(self.take())
            self.expect(Token.RPAR)
        return result

    def load_import(self):
        modname = self.take()
        name = self.take()
        self.expect(Token.LPAR)
        kind = self.take()
        if kind == 'func':
            id = self._parse_optional_id(default=self.gen_id('func'))
            if self.match(Token.LPAR, 'type'):
                self.expect(Token.LPAR, 'type')
                ref = self._parse_ref('type')  # Type reference
                self.expect(Token.RPAR)
            else:
                params, results = self._parse_function_signature()
                ref = self._add_or_reuse_type_definition(params, results)
            info = (ref,)
        elif kind == 'table':
            id = self._parse_optional_id(default=self.gen_id('table'))
            min, max = self.parse_limits()
            table_kind = self.take()
            assert table_kind == 'anyfunc'
            info = (table_kind, min, max)
        elif kind == 'memory':
            id = self._parse_optional_id(default=self.gen_id('memory'))
            min, max = self.parse_limits()
            info = (min, max)
        elif kind == 'global':
            id = self._parse_optional_id(default=self.gen_id('global'))
            typ, mutable = self.parse_global_type()
            info = (typ, mutable)
        else:  # pragma: no cover
            raise NotImplementedError(kind)

        self.expect(Token.RPAR, Token.RPAR)
        self.add_definition(
            components.Import(modname, name, kind, id, info))

    def load_export(self):
        """ Parse a toplevel export """
        name = self.take()
        self.expect(Token.LPAR)
        kind = self.take()
        ref = self._parse_ref(kind)
        self.expect(Token.RPAR, Token.RPAR)
        self.add_definition(
            components.Export(name, kind, ref))

    def load_start(self):
        """ Parse a toplevel start """
        name = self._parse_ref('func')
        self.expect(Token.RPAR)
        self.add_definition(components.Start(name))

    def load_table(self):
        """ Parse a table """
        id = self._parse_optional_id(default=self.gen_id('table'))
        self._parse_inline_export('table', id)
        if self.match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            min, max = self.parse_limits()
            kind = self.take()
            self.expect(Token.RPAR)
            info = (kind, min, max)
            self.add_definition(
                components.Import(modname, name, 'table', id, info))
        elif self.munch('anyfunc'):
            # We have embedded data
            self.expect(Token.LPAR, 'elem')
            refs = self.parse_ref_list()
            self.expect(Token.RPAR)
            self.expect(Token.RPAR)
            offset = [components.Instruction('i32.const', 0)]
            min = max = len(refs)
            self.add_definition(
                components.Table(id, 'anyfunc', min, max))
            table_ref = self._make_ref('table', id)
            self.add_definition(
                components.Elem(table_ref, offset, refs))
        else:
            min, max = self.parse_limits()
            kind = self.take()
            assert kind == 'anyfunc'
            self.expect(Token.RPAR)
            self.add_definition(
                components.Table(id, kind, min, max))

    def load_elem(self):
        """ Load an elem element """
        ref = self._parse_optional_ref('table', default=0)
        offset = self.parse_offset_expression()
        refs = self.parse_ref_list()
        while self._at_id():
            refs.append(self.take())
        self.expect(Token.RPAR)
        self.add_definition(
            components.Elem(ref, offset, refs))

    def parse_ref_list(self):
        """ Parse $1 $2 $foo $bar """
        refs = []
        while self._at_ref():
            ref = self.get_ref('func', self.take())
            refs.append(ref)
        return refs

    def get_ref(self, space, value):
        """ Get a reference to an object """
        return self._make_ref(space, value)

    def _make_ref(self, space, value):
        """ Create a reference in a space given a value """
        if is_dollar(value):
            ref = components.Ref(space, name=value)
            if space == 'local':
                self.func_backlog[-1].append(ref)
            elif space == 'label':
                # Lookup depth now:
                # Search backwards from top:
                depth = list(reversed(self.block_stack)).index(value)
                # depth = len(self.block_stack) - pos - 1
                ref.index = depth
            else:
                self.resolve_backlog.append(ref)
        else:
            ref = components.Ref(space, index=make_int(value))
        return ref

    def load_memory(self):
        """ Load a memory definition """
        id = self._parse_optional_id(default=self.gen_id('memory'))
        self._parse_inline_export('memory', id)
        if self.match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            min, max = self.parse_limits()
            self.expect(Token.RPAR)
            info = (min, max)
            self.add_definition(
                components.Import(modname, name, 'memory', id, info))
        elif self.munch(Token.LPAR, 'data'):  # Inline data
            data = self.parse_data_blobs()
            self.expect(Token.RPAR)
            self.expect(Token.RPAR)
            max = round_up(len(data), PAGE_SIZE) // PAGE_SIZE
            assert len(data) <= max * PAGE_SIZE, 'TODO: round upward'
            min = max
            self.add_definition(
                components.Memory(id, min, max))
            offset = [components.Instruction('i32.const', 0)]
            memory_ref = self._make_ref('memory', id)
            self.add_definition(components.Data(memory_ref, offset, data))
        else:
            min, max = self.parse_limits()
            self.expect(Token.RPAR)
            self.add_definition(
                components.Memory(id, min, max))

    def parse_limits(self):
        if is_int(self._lookahead(1)[0]):
            min = make_int(self.take())
            if is_int(self._lookahead(1)[0]):
                max = make_int(self.take())
            else:
                max = None
        else:
            min = 0
            max = None
        return min, max

    def parse_global_type(self):
        if self.munch(Token.LPAR, 'mut'):
            typ = self.take()
            mutable = True
            self.expect(Token.RPAR)
        else:
            typ = self.take()
            mutable = False
        return (typ, mutable)

    def load_global(self):
        """ Load a global definition """
        id = self._parse_optional_id(default=self.gen_id('global'))
        self._parse_inline_export('global', id)
        if self.match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            typ, mutable = self.parse_global_type()
            info = (typ, mutable)
            self.expect(Token.RPAR)
            self.add_definition(
                components.Import(modname, name, 'global', id, info))
        else:
            typ, mutable = self.parse_global_type()
            init = self._load_instruction_list()
            self.expect(Token.RPAR)
            self.add_definition(
                components.Global(id, typ, mutable, init))

    def load_data(self):
        """ Load data """
        ref = self._parse_optional_ref('memory', default=0)
        offset = self.parse_offset_expression()
        data = self.parse_data_blobs()
        self.expect(Token.RPAR)
        self.add_definition(
            components.Data(ref, offset, data))

    def parse_data_blobs(self):
        data = bytearray()
        while not self.match(Token.RPAR):
            txt = self.take()
            assert isinstance(txt, str)
            data.extend(datastring2bytes(txt))
        data = bytes(data)
        return data

    def parse_offset_expression(self):
        in_offset = self.munch(Token.LPAR, 'offset')
        assert self.at_instruction()
        offset = self._load_instruction_list()
        if in_offset:
            self.expect(Token.RPAR)
        return offset

    def load_func(self):
        id = self._parse_optional_id(default=self.gen_id('func'))
        self._parse_inline_export('func', id)

        if self.match(Token.LPAR, 'import'):  # handle inline imports
            modname, name = self._parse_inline_import()
            ref = self._parse_type_use()
            # TODO: wtf, parse types twice? why?
            params, results = self._parse_function_signature()
            self.expect(Token.RPAR)
            info = (ref,)
            self.add_definition(
                components.Import(modname, name, 'func', id, info))
        else:
            ref = self._parse_type_use()
            # TODO: wtf, parse types twice? why?
            params, results = self._parse_function_signature()
            localz = self._parse_locals()

            self.func_backlog.append([])
            self.block_stack = []
            instructions = self._load_instruction_list()
            assert not self.block_stack
            # for i in instructions:
            #    print(i.to_string())
            self.expect(Token.RPAR)
            self.add_definition(
                components.Func(id, ref, localz, instructions))

    def _parse_locals(self):
        return self._parse_type_bound_value_list('local')

    def _load_instruction_list(self):
        """ Load a list of instructions """
        instructions = []
        while self.at_instruction():
            instructions.extend(self._load_instruction())
        # print(instructions)
        return instructions

    def _load_instruction(self):
        """ Load a single (maybe nested) instruction """

        instructions = []
        # We can have instructions without parenthesis! OMG
        is_braced = self.munch(Token.LPAR)
        opcode = self.take()

        if opcode in ('block', 'loop', 'if'):
            block_id = self._parse_optional_id()
            self.block_stack.append(block_id)
            # Result type:
            if self.munch(Token.LPAR, 'result'):
                result = self.take()
                self.expect(Token.RPAR)
            elif self.munch('emptyblock'):
                # TODO: is this legit?
                result = 'emptyblock'
            else:
                result = 'emptyblock'

            if is_braced:
                if opcode == 'if':
                    # Maybe we have a then instruction?
                    if self.munch(Token.RPAR):
                        instructions.append(
                            components.BlockInstruction('if', block_id, result))
                    else:
                        # Nested stuff
                        # First is the condition:
                        if not self.match(Token.LPAR, 'then'):
                            instructions.extend(self._load_instruction())

                        instructions.append(
                            components.BlockInstruction('if', block_id, result))

                        if self.munch(Token.RPAR):
                            pass
                        else:
                            # Optionally a nested then:
                            if self.munch(Token.LPAR, 'then'):
                                body = self._load_instruction_list()
                                instructions.extend(body)
                                self.expect(Token.RPAR)

                            # Load body and optional 'else':
                            body = self._load_instruction_list()
                            instructions.extend(body)
                            self.expect(Token.RPAR)

                            # Add implicit end:
                            self.block_stack.pop()
                            instructions.append(components.Instruction('end'))
                else:
                    instructions.append(
                        components.BlockInstruction(opcode, block_id, result))
                    if self.munch(Token.RPAR):
                        pass
                    else:  # Nested instructions
                        body = self._load_instruction_list()
                        self.expect(Token.RPAR)
                        instructions.extend(body)

                    # Add implicit end:
                    self.block_stack.pop()
                    instructions.append(components.Instruction('end'))
            else:
                instructions.append(
                    components.BlockInstruction(opcode, block_id, result))

        elif opcode in ('else',):
            block_id = self._parse_optional_id()
            instructions.append(components.Instruction(opcode))
            if is_braced:
                if not self.munch(Token.RPAR):
                    # Nested instructions
                    instructions.extend(self._load_instruction_list())
                    self.expect(Token.RPAR)
        elif opcode in ('end',):
            block_id = self._parse_optional_id()
            matching_id = self.block_stack.pop()
            # lo(matching_id)
            # TODO: we can check this label with the start label
            if is_braced:
                self.expect(Token.RPAR)
            instructions.append(components.Instruction(opcode))
        else:
            # Process any special case arguments:
            if '.load' in opcode or '.store' in opcode:
                args = []
                while isinstance(self._lookahead(1)[0], str):
                    args.append(self.take())
            elif opcode == 'call_indirect':
                type_ref = self._parse_type_use()
                table_ref = components.Ref('table', index=0)
                args = (type_ref, table_ref)
                # TODO: wtf, parse types twice? why?
                params, results = self._parse_function_signature()
                # print(params, results)
                # TODO: compare unbound func signature with type?
            elif opcode in ('memory.grow', 'memory.size'):
                # Simply take all arguments possible:
                args = []
                while isinstance(self._lookahead(1)[0], (int, str)):
                    args.append(self.take())
            else:
                operands = OPERANDS[opcode]

                args = []
                for op in operands:
                    assert not self.match(Token.LPAR)
                    if op == 'br_table':
                        # Take all ints and strings as jump labels:
                        targets = []
                        while isinstance(self._lookahead(1)[0], (int, str)):
                            targets.append(self.get_ref('label', self.take()))
                        arg = targets
                    elif op == ArgType.LABELIDX:
                        kind = 'label'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.LOCALIDX:
                        kind = 'local'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.GLOBALIDX:
                        kind = 'global'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.FUNCIDX:
                        kind = 'func'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.TYPEIDX:
                        kind = 'type'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.TABLEIDX:
                        kind = 'table'
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    elif op == ArgType.I32:
                        arg = make_int(self.take(), bits=32)
                    elif op == ArgType.I64:
                        arg = make_int(self.take(), bits=64)
                    elif op == ArgType.F32:
                        arg = make_float(self.take())
                    elif op == ArgType.F64:
                        arg = make_float(self.take())
                    elif op == ArgType.U32:
                        arg = self.take()
                    elif op.endswith('idx'):
                        kind = op[:-3]
                        arg = self.take()
                        arg = self.get_ref(kind, arg)
                    else:
                        arg = self.take()

                    args.append(arg)

            # Nested instruction!
            if is_braced:
                while not self.match(Token.RPAR):
                    instructions.extend(self._load_instruction())
                self.expect(Token.RPAR)

            i = components.Instruction(opcode, *args)
            instructions.append(i)
        return instructions

    # Inline stuff:
    def _parse_inline_import(self):
        self.expect(Token.LPAR, 'import')
        modname = self.take()
        name = self.take()
        self.expect(Token.RPAR)
        return modname, name

    def _parse_inline_export(self, kind, obj_name):
        ref = self._make_ref(kind, obj_name)
        while self.match(Token.LPAR, 'export'):
            self.expect(Token.LPAR, 'export')
            name = self.take()
            self.expect(Token.RPAR)
            self.add_definition(
                components.Export(name, kind, ref))

    def at_instruction(self):
        if self.match(Token.LPAR):
            la = self._lookahead(2)[1]
        else:
            la = self._lookahead(1)[0]
        return la in OPCODES

    def _at_id(self):
        x = self._lookahead(1)[0]
        return is_id(x)

    def _at_ref(self):
        x = self._lookahead(1)[0]
        return is_ref(x)


def is_id(x):
    # TODO: is id of None a good plan?
    return is_dollar(x) or (x is None)


def is_ref(x):
    """ Is the given value a reference """
    return is_dollar(x) or is_int(x)


def is_dollar(x):
    return isinstance(x, str) and x.startswith('$')


def round_up(value, multiple):
    rest = value % multiple
    if rest:
        return value + (multiple - rest)
    else:
        return value
