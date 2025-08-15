"""Parse WAT (wasm text).

More or less a python version of this code:
https://github.com/WebAssembly/wabt/blob/master/src/wast-parser.cc
"""

import logging
from collections import defaultdict
from collections.abc import Iterable
from ...lang.sexpr import parse_sexpr
from ...lang.sexpr import SList, SSymbol, SString
from ...lang.common import SourceLocation
from ...lang.common import Token
from ...lang.tools.recursivedescent import RecursiveDescentParser
from ..opcodes import OPERANDS, OPCODES, ArgType
from ..util import datastring2bytes, make_int, make_float, is_int, PAGE_SIZE
from .util import default_alignment, log2
from .. import components


logger = logging.getLogger("wat")


def s_token(e, loc):
    return Token(e, e, loc)


def load_tuple(module, t):
    """Load contents of tuple t into module"""
    if not isinstance(t, tuple):
        raise TypeError(f"t must be tuple, not {type(t)}")

    loader = WatParser(module)

    if any(isinstance(e, components.Definition) for e in t):
        if not all(isinstance(e, components.Definition) for e in t):
            raise TypeError("All elements must be wasm components")

        for e in t:
            loader.add_definition(e)
        module.id = None
        module.definitions = loader.gather_definitions()
    else:
        loader.parse_module(tuple_to_tokens(t))


def tuple_to_tokens(t: tuple):
    # Parse nested strings at top level:
    loc = SourceLocation("?", 1, 1, 1)
    yield s_token("(", loc)
    for e in t:
        if isinstance(e, str) and e.startswith("("):
            e = parse_sexpr(e)
            for x in _s_expr_generator_inner(e):
                yield x
        elif isinstance(e, tuple):
            for x in _tuple_generator_inner(e, loc):
                yield x
        else:
            raise NotImplementedError(str(e))
    yield s_token(")", loc)
    yield s_token("EOF", loc)


def _tuple_generator_inner(s: tuple, loc):
    yield s_token("(", loc)
    for e in s:
        if isinstance(e, tuple):
            yield from _tuple_generator_inner(e, loc)
        elif isinstance(e, (str, int)) or e is None:
            yield Token("word", e, loc)
        else:
            raise NotImplementedError(str(e))
    yield s_token(")", loc)


def s_expr_to_tokens(s_expr: SList):
    yield from _s_expr_generator_inner(s_expr)
    yield s_token("EOF", s_expr.loc)


def _s_expr_generator_inner(s_expr: SList):
    yield s_token("(", s_expr.loc)
    for e in s_expr:
        if isinstance(e, SList):
            yield from _s_expr_generator_inner(e)
        elif isinstance(e, SSymbol):
            yield Token("word", e.value, e.loc)
        elif isinstance(e, SString):
            yield Token("string", e.value, e.loc)
        else:
            raise NotImplementedError(str(e))
    yield s_token(")", s_expr.loc)


def load_s_expr(module, s):
    """First, flatten the S-expression"""
    tokens = s_expr_to_tokens(s)
    load_from_s_tokens(module, tokens)


def load_from_s_tokens(module, tokens):
    loader = WatParser(module)
    loader.parse_module(tokens)


class WatParser(RecursiveDescentParser):
    """WebAssembly text format parser."""

    def __init__(self, module):
        super().__init__()
        self.module = module
        self.definitions = defaultdict(list)
        self._type_hash = {}  # (params, results) -> ref
        self.counters = {
            "type": 0,
            "func": 0,
            "table": 0,
            "memory": 0,
            "global": 0,
            "elem": 0,
            "data": 0,
        }

        self.resolve_backlog = []
        self.func_backlog = []

    def parse_module(self, tokens: Iterable[Token]):
        """Parse a module from series of tokens"""
        self.init_lexer(tokens)

        self.expect("(")
        if self.munch("module"):
            # Detect id:
            self.module.id = self._parse_optional_id()
        else:
            self.module.id = None

        while self.munch("("):
            kind = self.take()
            if kind == "type":
                self.parse_type()
            elif kind == "data":
                self.parse_data()
            elif kind == "elem":
                self.parse_elem()
            elif kind == "export":
                self.parse_export()
            elif kind == "func":
                self.parse_func()
            elif kind == "global":
                self.parse_global()
            elif kind == "import":
                self.load_import()
            elif kind == "memory":
                self.parse_memory()
            elif kind == "start":
                self.parse_start()
            elif kind == "table":
                self.parse_table()
            else:  # pragma: no cover
                raise NotImplementedError(kind)
            self.expect(")")

        self.expect(")")
        self.expect("EOF")

        self.resolve_references()
        self.module.definitions = self.gather_definitions()

    def resolve_references(self):
        id_maps = {
            "type": {},
            "func": {},
            "table": {},
            "memory": {},
            "global": {},
            "elem": {},
            "data": {},
        }
        counters = {
            "type": 0,
            "func": 0,
            "table": 0,
            "memory": 0,
            "global": 0,
            "elem": 0,
            "data": 0,
        }

        # TODO: maybe this is not needed at this point?
        # Fill imports and other objects:
        for d in self.definitions["import"]:
            id_map = id_maps[d.kind]
            assert d.id not in id_map
            id_map[d.id] = counters[d.kind]
            counters[d.kind] += 1

        for space in [
            "type",
            "global",
            "memory",
            "table",
            "func",
            "elem",
            "data",
        ]:
            id_map = id_maps[space]
            for d in self.definitions[space]:
                assert d.id not in id_map
                id_map[d.id] = counters[space]
                counters[space] += 1

        # resolve any unresolved items:
        for item in self.resolve_backlog:
            item.index = item.resolve(id_maps)

        # Resolve inside functions:
        assert len(self.func_backlog) == len(self.definitions["func"])
        for bl, func in zip(self.func_backlog, self.definitions["func"]):
            # Fill map with local id's:
            type_idx = func.ref.resolve(id_maps)
            func_type = self.definitions["type"][type_idx]
            id_maps["local"] = dict(
                (param[0], i) for i, param in enumerate(func_type.params)
            )
            for i, lokal in enumerate(
                func.locals, start=len(func_type.params)
            ):
                if is_dollar(lokal[0]):
                    id_maps["local"][lokal[0]] = i

            for item in bl:
                item.index = item.resolve(id_maps)

    def gather_definitions(self):
        """Take all definitions by section id order:"""
        definitions = []
        for name in components.SECTION_IDS:
            for definition in self.definitions[name]:
                definitions.append(definition)
        return definitions

    def add_definition(self, definition):
        space = definition.__name__
        nr = len(self.definitions[space])
        self.definitions[space].append(definition)
        logger.debug(f"Parsed {definition} {nr}")

    def gen_id(self, kind):
        id = self.counters[kind]
        self.counters[kind] += 1
        return f"${id}"

    # Section types:
    def parse_type(self):
        """Load a tuple starting with 'type'"""
        id = self._parse_optional_id(default=self.gen_id("type"))
        self.expect("(", "func")
        params, results = self._parse_function_signature()
        self.expect(")")
        # Note cannot reuse type here unless we remap the id whereever
        # it is used
        self.add_definition(components.Type(id, params, results))

    def _parse_optional_id(self, default=None):
        id = self.take() if self._at_id() else default
        return id

    def _parse_use_or_default(self, space, default=None):
        """Parse an optional use, defaulting to 0"""
        if self.munch("(", space):
            value = self._parse_ref(space)
            self.expect(")")
        elif default is None:
            self.error("Expected space usage")
        else:
            value = self._make_ref(space, default)
        return value

    def _parse_ref(self, space, default=None):
        """Parse a reference (int or $ref) into the given space"""
        tok = self.next_token()
        if is_ref(tok.val):
            return self._make_ref(space, tok.val)
        elif default is None:
            self.error("Expected reference ($name or integer)", tok.loc)
        else:
            self.backup_token(tok)
            return self._make_ref(space, default)

    def _add_or_reuse_type_definition(self, params, results):
        key = tuple(params), tuple(results)
        ref = self._type_hash.get(key, None)
        if ref is None:
            type_id = self.gen_id("type")
            self.add_definition(components.Type(type_id, params, results))
            ref = self._make_ref("type", type_id)
            self._type_hash[key] = ref
        return ref

    def _parse_type_use(self):
        if self.match("(", "type"):
            ref = self._parse_type_ref()
        elif self.match("(", "param") or self.match("(", "result"):
            params, results = self._parse_function_signature()
            ref = self._add_or_reuse_type_definition(params, results)
        else:
            ref = self._add_or_reuse_type_definition([], [])
        return ref

    def _parse_type_ref(self):
        """Parse a type reference."""
        self.expect("(", "type")
        ref = self._parse_ref("type")
        self.expect(")")

        # Parse trailing check up of signature:
        if self.match("(", "param") or self.match("(", "result"):
            params, results = self._parse_function_signature()
            # TODO: check this with the type ref?

        return ref

    def _parse_function_signature(self):
        """Parse a function signature.

        For example: (param f64 i32) (result i64 f32 f32)
        """
        params = self._parse_param_list()
        results = self._parse_result_list()
        return params, results

    def _parse_param_list(self):
        """Parse (param i32 i32) and friends."""
        return self._parse_type_bound_value_list("param")

    def _parse_type_bound_value_list(self, kind):
        """Parse thing like (locals i32) (locals $foo i32)"""
        params = []
        while self.munch("(", kind):
            if not self.match(")"):
                if self._at_id():  # (param $id i32)
                    params.append((self.take(), self.take()))
                else:
                    # anonymous (param i32 i32 i32)
                    while not self.match(")"):
                        p = self.take()
                        params.append((len(params), p))
            self.expect(")")
        return params

    def _parse_result_list(self):
        result = []
        while self.munch("(", "result"):
            while not self.match(")"):
                result.append(self.take())
            self.expect(")")
        return result

    def load_import(self):
        """Parse top level import."""
        modname = self.take()
        name = self.take()
        self.expect("(")
        kind = self.take()
        id = self._parse_optional_id(default=self.gen_id(kind))
        if kind == "func":
            ref = self._parse_type_use()
            info = (ref,)
        elif kind == "table":
            min, max = self.parse_limits()
            table_kind = self.parse_reftype()
            info = (table_kind, min, max)
        elif kind == "memory":
            min, max = self.parse_limits()
            info = (min, max)
        elif kind == "global":
            typ, mutable = self.parse_global_type()
            info = (typ, mutable)
        else:  # pragma: no cover
            raise NotImplementedError(kind)

        self.expect(")")
        self.add_definition(components.Import(modname, name, kind, id, info))

    def parse_export(self):
        """Parse a toplevel export"""
        name = self.take()
        self.expect("(")
        kind = self.take()
        ref = self._parse_ref(kind)
        self.expect(")")
        self.add_definition(components.Export(name, kind, ref))

    def parse_start(self):
        """Parse a toplevel start"""
        name = self._parse_ref("func")
        self.add_definition(components.Start(name))

    def parse_table(self):
        """Parse a table"""
        id = self._parse_optional_id(default=self.gen_id("table"))
        self._parse_inline_export("table", id)
        if self.match("(", "import"):  # handle inline imports
            modname, name = self._parse_inline_import()
            info = self.parse_table_type()
            self.add_definition(
                components.Import(modname, name, "table", id, info)
            )
        elif self.match("funcref") or self.match("externref"):
            kind = self.parse_reftype()
            # We have embedded data
            self.expect("(", "elem")
            if self.match("(", "item") or self.at_instruction():
                refs = self.parse_item_list()
            else:
                refs = self.parse_ref_list()
            self.expect(")")
            offset = [components.Instruction("i32.const", 0)]
            min = max = len(refs)
            self.add_definition(components.Table(id, kind, min, max))
            table_ref = self._make_ref("table", id)
            mode = table_ref, offset
            eid = self.gen_id("elem")
            self.add_definition(components.Elem(eid, mode, refs))
        else:
            kind, min, max = self.parse_table_type()
            self.add_definition(components.Table(id, kind, min, max))

    def parse_table_type(self):
        """Parse table limits followed by reftype"""
        min, max = self.parse_limits()
        reftype = self.parse_reftype()
        info = (reftype, min, max)
        return info

    def parse_elem(self):
        """Load an element to fill a table"""
        id = self._parse_optional_id(default=self.gen_id("elem"))
        if self.match("(", "table"):
            ref = self._parse_use_or_default("table")
            offset = self.parse_offset_expression()
            mode = ref, offset
        elif self.match("(", "offset") or self.at_instruction():
            ref = components.Ref("table", index=0)
            offset = self.parse_offset_expression()
            mode = ref, offset
        elif self.match("declare"):
            self.expect("declare")
            mode = None  # Declare mode
        else:
            mode = None  # passive mode

        reftype, refs = self.parse_elem_list()
        self.add_definition(components.Elem(id, mode, refs))

    def parse_elem_list(self):
        tok = self.next_token()
        if tok.val == "funcref" or tok.val == "externref":
            reftype = tok.val
            refs = self.parse_item_list()
        elif tok.val == "func":
            reftype = "funcref"
            refs = self.parse_ref_list()
        elif is_ref(tok.val):
            self.backup_token(tok)
            reftype = "funcref"
            refs = self.parse_ref_list()
        elif tok.typ == ")":
            self.backup_token(tok)
            reftype = "funcref"
            refs = []
        else:
            self.error("Expected funcref/externref/func", tok.loc)
        return reftype, refs

    def parse_item_list(self):
        refs = []
        while True:
            if self.match("(", "item"):
                self.expect("(", "item")
                ref = self._load_instruction()
                self.expect(")")
            elif self.at_instruction():
                ref = self._load_instruction()
            else:
                break
            refs.append(ref)
        return refs

    def parse_ref_list(self):
        """Parse $1 $2 $foo $bar"""
        refs = []
        while self._at_ref():
            ref = self._parse_ref("func")
            refs.append(ref)
        return refs

    def _make_ref(self, space, value):
        """Create a reference in a space given a value"""
        if is_dollar(value):
            ref = components.Ref(space, name=value)
            if space == "local":
                self.func_backlog[-1].append(ref)
            elif space == "label":
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

    def parse_memory(self):
        """Load a memory definition"""
        id = self._parse_optional_id(default=self.gen_id("memory"))
        self._parse_inline_export("memory", id)
        if self.match("(", "import"):  # handle inline imports
            modname, name = self._parse_inline_import()
            min, max = self.parse_limits()
            info = (min, max)
            self.add_definition(
                components.Import(modname, name, "memory", id, info)
            )
        elif self.munch("(", "data"):  # Inline data
            data = self.parse_data_blobs()
            self.expect(")")
            max = round_up(len(data), PAGE_SIZE) // PAGE_SIZE
            assert len(data) <= max * PAGE_SIZE, "TODO: round upward"
            min = max
            self.add_definition(components.Memory(id, min, max))
            offset = [components.Instruction("i32.const", 0)]
            memory_ref = self._make_ref("memory", id)
            mode = (memory_ref, offset)
            data_id = self.gen_id("data")
            self.add_definition(components.Data(data_id, mode, data))
        else:
            min, max = self.parse_limits()
            self.add_definition(components.Memory(id, min, max))

    def parse_limits(self):
        if is_int(self.look_ahead(0).val):
            min = make_int(self.take())
            if is_int(self.look_ahead(0).val):
                max = make_int(self.take())
            else:
                max = None
        else:
            min = 0
            max = None
        return min, max

    def parse_global_type(self):
        if self.munch("(", "mut"):
            typ = self.take()
            mutable = True
            self.expect(")")
        else:
            typ = self.take()
            mutable = False
        return (typ, mutable)

    def parse_global(self):
        """Load a global definition"""
        id = self._parse_optional_id(default=self.gen_id("global"))
        self._parse_inline_export("global", id)
        if self.match("(", "import"):  # handle inline imports
            modname, name = self._parse_inline_import()
            typ, mutable = self.parse_global_type()
            info = (typ, mutable)
            self.add_definition(
                components.Import(modname, name, "global", id, info)
            )
        else:
            typ, mutable = self.parse_global_type()
            init = self._load_instruction_list()
            self.add_definition(components.Global(id, typ, mutable, init))

    def parse_data(self):
        """Load data segment"""
        id = self._parse_optional_id(default=self.gen_id("data"))
        if self.peek == ")":
            mode = None
            data = bytes()
        else:
            if self.peek == "string":
                # Passive block
                mode = None
            else:
                # Active block
                ref = self._parse_use_or_default("memory", default=0)
                offset = self.parse_offset_expression()
                mode = (ref, offset)
            data = self.parse_data_blobs()
        definition = components.Data(id, mode, data)
        self.add_definition(definition)

    def parse_data_blobs(self) -> bytes:
        data = bytearray()
        while not self.match(")"):
            txt = self.take()
            if isinstance(txt, bytes):
                blob = txt
            else:
                assert isinstance(txt, str)
                blob = datastring2bytes(txt)
            data.extend(blob)
        return bytes(data)

    def parse_offset_expression(self):
        if self.munch("(", "offset"):
            offset = self._load_instruction_list()
            self.expect(")")
        else:
            offset = self._load_instruction()
        return offset

    def parse_func(self):
        """Load a single function definition."""
        id = self._parse_optional_id(default=self.gen_id("func"))
        self._parse_inline_export("func", id)

        if self.match("(", "import"):  # handle inline imports
            modname, name = self._parse_inline_import()
            ref = self._parse_type_use()
            info = (ref,)
            self.add_definition(
                components.Import(modname, name, "func", id, info)
            )
        else:
            ref = self._parse_type_use()
            localz = self._parse_locals()
            self.func_backlog.append([])
            self.block_stack = []
            instructions = self._load_instruction_list()
            assert not self.block_stack
            self.add_definition(components.Func(id, ref, localz, instructions))

    def _parse_locals(self):
        return self._parse_type_bound_value_list("local")

    def _load_instruction_list(self):
        """Load a list of instructions"""
        instructions = []
        while self.at_instruction():
            instructions.extend(self._load_instruction())
        return instructions

    def _load_instruction(self):
        """Load a single (maybe nested) instruction.

        For nesting syntax, please refer here:
        https://webassembly.github.io/spec/core/text/instructions.html#folded-instructions

        Note that this returns a list of instructions.
        """

        instructions = []
        # We can have instructions without parenthesis! OMG
        is_braced = self.munch("(")
        tok = self.next_token()
        opcode = tok.val
        opcode_loc = tok.loc

        if opcode == "if":
            block_id = self._parse_optional_id()
            self.block_stack.append(block_id)
            block_type = self._load_block_type()
            if_instruction = components.BlockInstruction(
                "if", block_id, block_type
            )

            if is_braced:
                # Nested/folded syntax stuff
                # 'then' is no opcode, solely syntactic sugar.

                # First is the condition:
                instructions.extend(self._load_instruction_list())
                instructions.append(if_instruction)

                # A nested then:
                self.expect("(", "then")
                instructions.extend(self._load_instruction_list())
                self.expect(")")

                # Optional nested 'else':
                if self.munch("(", "else"):
                    instructions.append(components.Instruction("else"))
                    instructions.extend(self._load_instruction_list())
                    self.expect(")")

                # Add implicit end:
                self.block_stack.pop()
                instructions.append(components.Instruction("end"))
            else:
                instructions.append(if_instruction)

        elif opcode in ("block", "loop"):
            block_id = self._parse_optional_id()
            self.block_stack.append(block_id)
            block_type = self._load_block_type()

            instructions.append(
                components.BlockInstruction(opcode, block_id, block_type)
            )

            if is_braced:
                # Nested instructions
                instructions.extend(self._load_instruction_list())

                # Add implicit end:
                self.block_stack.pop()
                instructions.append(components.Instruction("end"))

        elif opcode == "else":
            block_id = self._parse_optional_id()
            self._check_block_ids(self.block_stack[-1], block_id, opcode_loc)

            instructions.append(components.Instruction(opcode))
            assert not is_braced

        elif opcode == "end":
            block_id = self._parse_optional_id()
            matching_id = self.block_stack.pop()
            self._check_block_ids(matching_id, block_id, opcode_loc)

            instructions.append(components.Instruction(opcode))

        else:
            if opcode not in OPCODES:
                self.error("Expected instruction", loc=opcode_loc)
            args = self._gather_opcode_arguments(opcode)
            i = components.Instruction(opcode, *args)

            if is_braced:
                # Nested instruction!
                instructions.extend(self._load_instruction_list())

            instructions.append(i)

        # Parse matching closing brace:
        if is_braced:
            self.expect(")")

        return instructions

    def _check_block_ids(self, ref_block_id, block_id, loc):
        if block_id is not None:
            if block_id != ref_block_id:
                self.error("Block id mismatch", loc)

    def _load_block_type(self):
        """Get the block type."""
        if self.munch("emptyblock"):
            # TODO: is this legit?
            block_type = "emptyblock"
        elif self.match("(", "type"):
            block_type = self._parse_type_ref()
        else:
            params, results = self._parse_function_signature()
            if len(params) == 0 and len(results) == 1:
                # single result special case
                block_type = results[0]
            elif len(params) == 0 and len(results) == 0:
                block_type = "emptyblock"
            else:
                # Create type ID
                ref = self._add_or_reuse_type_definition(params, results)
                block_type = ref
        return block_type

    def parse_reftype(self):
        tok = self.next_token()
        reftype = tok.val
        if reftype in ["funcref", "externref"]:
            return reftype
        else:
            self.error("Expected ref-type", tok.loc)

    def _parse_heaptype(self):
        tok = self.next_token()
        reftype = tok.val
        if reftype in ["func", "extern"]:
            return reftype
        else:
            self.error("Expected ref-type", tok.loc)

    def _gather_opcode_arguments(self, opcode):
        """Gather the arguments to a specific opcode."""
        # Process any special case arguments:
        if ".load" in opcode or ".store" in opcode:
            args = self._parse_load_store_arguments(opcode)
        elif opcode == "call_indirect":
            # Note: table_ref and type_ref are swapped in binary format:
            table_ref = self._parse_ref("table", default=0)
            type_ref = self._parse_type_use()
            args = (type_ref, table_ref)
            # TODO: compare unbound func signature with type?
        elif opcode == "table.init":
            if is_ref(self.look_ahead(1).val):
                table_ref = self._parse_ref("table")
            else:
                table_ref = self._make_ref("table", 0)
            elem_ref = self._parse_ref("elem")
            args = (table_ref, elem_ref)
        elif opcode == "select":
            # Parse optional result type of select instruction
            result_type = self._parse_result_list()
            args = (result_type,)
        else:
            operands = OPERANDS[opcode]
            args = self._parse_operands(operands)

        return args

    def _parse_operands(self, operands):
        args = []
        for op in operands:
            if op == ArgType.LABELIDX:
                arg = self._parse_ref("label")
            elif op == ArgType.LOCALIDX:
                arg = self._parse_ref("local")
            elif op == ArgType.GLOBALIDX:
                arg = self._parse_ref("global")
            elif op == ArgType.FUNCIDX:
                arg = self._parse_ref("func")
            elif op == ArgType.TYPEIDX:
                arg = self._parse_ref("type")
            elif op == ArgType.TABLEIDX:
                arg = self._parse_ref("table", default=0)
            elif op == ArgType.ELEMIDX:
                arg = self._parse_ref("elem")
            elif op == ArgType.DATAIDX:
                arg = self._parse_ref("data")
            elif op == ArgType.HEAPTYPE:
                arg = self._parse_heaptype()
            elif op == ArgType.I32:
                arg = make_int(self.take(), bits=32)
            elif op == ArgType.I64:
                arg = make_int(self.take(), bits=64)
            elif op == ArgType.F32 or op == ArgType.F64:
                arg = make_float(self.take())
            elif op == ArgType.U32:
                arg = self.take()
            elif op == "br_table":
                # Take all ints and strings as jump labels:
                targets = []
                while self._at_ref():
                    targets.append(self._parse_ref("label"))
                arg = targets
            elif op == ArgType.U8:
                # one day, this byte argument might be used
                # to indicate which memory to access.
                arg = 0
            else:
                raise NotImplementedError(str(op))

            args.append(arg)
        return args

    def _parse_load_store_arguments(self, opcode):
        """Parse arguments to a load and store instruction.

        Memory instructions have keyword args in text format :/
        """

        # Determine default args
        offset_arg = 0
        align_arg = default_alignment(opcode)

        # Parse keyword args
        attributes = self._parse_keyword_arguments()
        for key, value in attributes.items():
            value = str2int(value)
            if key == "align":
                # Store alignment as power of 2:
                align_arg = log2(value)
            elif key == "offset":
                offset_arg = value

        args = align_arg, offset_arg
        return args

    def _parse_keyword_arguments(self):
        """Parse some arguments of shape key=value."""
        attributes = {}
        while is_kwarg(self.look_ahead(0).val):
            arg = self.take()
            assert is_kwarg(arg)
            key, value = arg.split("=", 1)
            assert key not in attributes
            attributes[key] = value
        return attributes

    # Inline stuff:
    def _parse_inline_import(self):
        self.expect("(", "import")
        modname = self.take()
        name = self.take()
        self.expect(")")
        return modname, name

    def _parse_inline_export(self, kind, obj_name):
        ref = self._make_ref(kind, obj_name)
        while self.munch("(", "export"):
            name = self.take()
            self.expect(")")
            self.add_definition(components.Export(name, kind, ref))

    def at_instruction(self):
        if self.match("("):
            la = self.look_ahead(1).val
        else:
            la = self.look_ahead(0).val
        return la in OPCODES

    def match(self, *args):
        """Test if we match"""
        for i, arg in enumerate(args):
            tok = self.look_ahead(i)
            if not self.is_ok_tok(tok, arg):
                return False
        return True

    def munch(self, *args) -> bool:
        """If we match the given tokens, consume the tokens"""
        if self.match(*args):
            for _ in args:
                self.next_token()
            return True
        else:
            return False

    def expect(self, *args):
        """Consume the token types"""
        for arg in args:
            tok = self.next_token()
            if not self.is_ok_tok(tok, arg):
                self.error(f"Got {tok.val}, expected: {arg}", tok.loc)

    @staticmethod
    def is_ok_tok(tok, arg):
        if tok is None:
            return False
        if arg in ("(", ")", "EOF"):
            return tok.typ == arg
        else:
            return tok.typ == "word" and tok.val == arg

    def take(self):
        """Consume the next token, and return its value"""
        tok = self.next_token()
        return tok.val

    def _at_id(self):
        x = self.look_ahead(0).val
        return is_id(x)

    def _at_ref(self):
        x = self.look_ahead(0).val
        return is_ref(x)


def is_id(x):
    """Check if x can be an id"""
    return is_dollar(x)


def is_ref(x):
    """Is the given value a reference"""
    return is_dollar(x) or is_int(x)


def is_dollar(x):
    return isinstance(x, str) and x.startswith("$")


def is_kwarg(x):
    """return if x is something like 'offset=12'"""
    return isinstance(x, str) and "=" in x


def round_up(value, multiple):
    rest = value % multiple
    if rest:
        return value + (multiple - rest)
    else:
        return value


def str2int(x):
    return int(x, 16) if x.startswith("0x") else int(x)
