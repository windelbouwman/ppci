""" Functionality to read a wasm module from it's binary format.

"""


import logging
import struct
from contextlib import contextmanager
from io import BytesIO
from ...utils.leb128 import unsigned_leb128_decode, signed_leb128_decode
from ..opcodes import ArgType, OPERANDS, REVERZ
from ..components import Ref, Instruction, SECTION_IDS, DEFINITION_CLASSES
from .. import components
from .io import LANG_TYPES_REVERSE


logger = logging.getLogger("wasm")


class BinaryFileReader:
    """ Reader which can read binary wasm. """

    def __init__(self, f):
        self._f = [f]
        self._buffer = bytes()
        self._pos = 0

        self._section_id_to_name = {}
        for name, id in SECTION_IDS.items():
            if name != "code":  # use "func" instead
                self._section_id_to_name[id] = name

    def read_module(self, module):
        """ Load a module from wasm binary format. """
        self.read_header()

        # Prepare
        self._type4func = {}
        self._id_maps = {
            "type": {},
            "func": {},
            "table": {},
            "memory": {},
            "global": {},
        }

        # todo: we may assign id's inside the _from_reader() methods,
        # revisit when implementing the custom name section.

        # Read sections that contain definitions
        self._definitions = []
        while True:
            try:
                section_id = self.read_byte()
            except EOFError:
                break

            section_data = self.read_length_prefixed_bytes()
            with self.push_data(section_data):
                self.read_section(section_id)

        logger.info(
            "Loaded WASM module from binary with %i definitions"
            % len(self._definitions)
        )
        module.definitions = self._definitions
        module.id = None

    def read_section(self, section_id):
        """ Process a single section. """
        section_name = self._section_id_to_name[section_id]
        logger.debug("Loading %s section", section_name)

        if section_name == "function":
            self.read_function_prototypes()
        elif section_name == "start":  # There is (at most) 1 start def
            self._definitions.append(self.read_start_definition())
        elif section_name == "custom":
            self._definitions.append(self.read_custom_definition())
        else:
            ndefs = self.read_uint()  # for this section
            for i in range(ndefs):
                if section_name == "func":
                    d = self.read_func_definition(i)
                else:
                    Cls = DEFINITION_CLASSES[section_name]
                    d = self.read_definition(Cls)

                self._definitions.append(d)
                if section_name == "import":
                    id_map = self._id_maps[d.kind]
                    assert d.id in id_map
                elif section_name in self._id_maps:
                    id_map = self._id_maps[section_name]
                    assert d.id in id_map

    def read_header(self):
        """ Check header and version """
        data = self.read_exactly(4)
        if data != b"\x00asm":
            raise ValueError("Magic wasm marker is invalid")
        version = self.read_u32()
        assert version == 1, version

    def read_function_prototypes(self):
        # Read mapping of func id to type id (both indexes)
        nfuncs = self.read_uint()
        for i in range(nfuncs):
            self._type4func[i] = self.read_uint()

    def read_definition(self, cls):
        mp = {
            components.Type: self.read_type_definition,
            components.Import: self.read_import_definition,
            components.Table: self.read_table_definition,
            components.Memory: self.read_memory_definition,
            components.Global: self.read_global_definition,
            components.Export: self.read_export_definition,
            components.Start: self.read_start_definition,
            components.Elem: self.read_elem_definition,
            components.Data: self.read_data_definition,
        }
        return mp[cls]()

    def read_exactly(self, amount=None):
        if amount is not None and amount < 0:
            raise ValueError("Cannot read {} bytes".format(amount))
        data = self._f[-1].read(amount)
        if amount is not None and len(data) != amount:
            raise EOFError("Reading beyond end of file")
        return data

    @contextmanager
    def push_data(self, data):
        """ Process the given data first.
        """
        self._f.append(BytesIO(data))
        yield
        f = self._f.pop()
        remaining = f.read()
        assert remaining == bytes(), str(remaining)

    def read_fmt(self, fmt):
        """ Read data according to the given format. """
        size = struct.calcsize(fmt)
        data = self.read_exactly(size)
        return struct.unpack(fmt, data)[0]

    def bytefile(self, f):
        b = f.read(1)
        while b:
            yield b[0]
            b = f.read(1)

    def __next__(self):
        b = self.read_exactly(1)
        return b[0]

    def read_byte(self):
        """ Read the value of a single byte """
        data = self.read_exactly(1)
        return data[0]

    def read_int(self):
        """ Read variable size signed int """
        return signed_leb128_decode(self)

    def read_uint(self):
        """ Read variable size unsigned integer """
        return unsigned_leb128_decode(self)

    def read_f32(self) -> float:
        """ Read a single f32 value """
        return self.read_fmt("f")

    def read_f64(self) -> float:
        """ Read a single f64 value """
        return self.read_fmt("d")

    def read_u32(self) -> int:
        """ Read a single u32 value """
        return self.read_fmt("<I")

    def read_length_prefixed_bytes(self) -> bytes:
        """ Read length prefixed raw bytes data """
        amount = self.read_uint()
        return self.read_exactly(amount)

    def read_str(self):
        """ Read a string """
        data = self.read_length_prefixed_bytes()
        return data.decode("utf-8")

    def read_type(self):
        """ Read a wasm type """
        tp = self.read_byte()
        return LANG_TYPES_REVERSE[tp]

    def read_limits(self):
        """ Read min and max limits """
        mx_present = self.read_byte()
        assert mx_present in [0, 1]
        minimum = self.read_uint()
        if mx_present:
            maximum = self.read_uint()
        else:
            maximum = None
        return minimum, maximum

    def read_space_ref(self, space):
        """ Read a reference into a certain space. """
        return Ref(space, index=self.read_uint())

    def gen_id(self, space):
        return len(self._id_maps[space])

    def add_definition(self, space, definition):
        assert isinstance(definition.id, int)
        id_map = self._id_maps[space]
        assert definition.id not in id_map
        id_map[definition.id] = definition

    def read_expression(self):
        """ Read instructions until an end marker is found """
        expr = []
        blocks = 1
        i = self.read_instruction()
        # keep track of if/block/loop etc:
        if i.opcode == "end":
            blocks -= 1
        elif i.opcode in ("if", "block", "loop"):
            blocks += 1
        expr.append(i)
        while blocks:
            i = self.read_instruction()
            # print(i)
            if i.opcode == "end":
                blocks -= 1
            elif i.opcode in ("if", "block", "loop"):
                blocks += 1
            expr.append(i)

        # Strip of last end opcode:
        assert expr[-1].opcode == "end"
        return expr[:-1]

    def read_instruction(self):
        """ Read a single instruction """
        binopcode = self.read_byte()
        opcode = REVERZ[binopcode]
        operands = OPERANDS[opcode]
        # print(opcode, type, operands)
        args = []
        for operand in operands:
            if operand in rfm:
                arg = rfm[operand](self)
            elif operand == "byte":
                arg = self.read_byte()
            elif operand == "br_table":
                count = self.read_uint()
                vec = []
                for _ in range(count + 1):
                    idx = self.read_space_ref("label")
                    vec.append(idx)
                arg = vec
            else:  # pragma: no cover
                raise NotImplementedError(operand)
            args.append(arg)
        args = tuple(args)

        block_types = ("block", "loop", "if")
        if opcode in block_types:
            instruction = components.BlockInstruction(opcode, *args)
        else:
            instruction = Instruction(opcode, *args)
        return instruction

    def read_type_definition(self):
        """ Read a type definition. """
        form = self.read_exactly(1)
        assert form == b"\x60"
        num_params = self.read_uint()
        params = [(i, self.read_type()) for i in range(num_params)]
        num_returns = self.read_uint()
        results = [self.read_type() for _ in range(num_returns)]
        id = self.gen_id("type")
        definition = components.Type(id, params, results)
        self.add_definition("type", definition)
        return definition

    def read_import_definition(self):
        """ Fill an import. """
        modname = self.read_str()
        name = self.read_str()
        kind_id = self.read_byte()
        if kind_id == 0:
            kind = "func"
            info = (self.read_space_ref("type"),)
        elif kind_id == 1:
            kind = "table"
            table_kind = self.read_type()
            min, max = self.read_limits()
            info = table_kind, min, max
        elif kind_id == 2:
            kind = "memory"
            min, max = self.read_limits()
            info = min, max
        elif kind_id == 3:
            kind = "global"
            info = self.read_type(), bool(self.read_byte())
        else:  # pragma: no cover
            raise NotImplementedError()
        id = self.gen_id(kind)
        definition = components.Import(modname, name, kind, id, info)
        self.add_definition(kind, definition)
        return definition

    def read_table_definition(self):
        kind = self.read_type()
        assert kind == "funcref"
        table_min, table_max = self.read_limits()
        id = self.gen_id("table")
        definition = components.Table(id, kind, table_min, table_max)
        self.add_definition("table", definition)
        return definition

    def read_memory_definition(self):
        memory_min, memory_max = self.read_limits()
        id = self.gen_id("memory")
        definition = components.Memory(id, memory_min, memory_max)
        self.add_definition("memory", definition)
        return definition

    def read_global_definition(self):
        typ = self.read_type()
        mutable = bool(self.read_byte())
        init = self.read_expression()
        id = self.gen_id("global")
        definition = components.Global(id, typ, mutable, init)
        self.add_definition("global", definition)
        return definition

    def read_export_definition(self):
        """ Read an `export` definition. """
        name = self.read_str()
        kind_id = self.read_byte()
        kind = ["func", "table", "memory", "global"][kind_id]
        ref = self.read_space_ref(kind)
        return components.Export(name, kind, ref)

    def read_start_definition(self):
        ref = self.read_space_ref("func")
        return components.Start(ref)

    def read_elem_definition(self):
        """ Read an `elem` definition. """
        ref = self.read_space_ref("table")
        offset = self.read_expression()

        count = self.read_uint()
        refs = [self.read_space_ref("func") for _ in range(count)]
        return components.Elem(ref, offset, refs)

    def read_func_definition(self, index):
        """ Read a function with locals and instructions. """
        # First read on the function body block:
        body_data = self.read_length_prefixed_bytes()

        with self.push_data(body_data):
            num_local_pairs = self.read_uint()
            localz = []
            for _ in range(num_local_pairs):
                c = self.read_uint()
                t = self.read_type()
                localz.extend([(None, t)] * c)
            instructions = self.read_expression()

        # Function type ref:
        ref = Ref("type", index=self._type4func[index])

        id = self.gen_id("func")
        func = components.Func(id, ref, localz, instructions)
        self.add_definition("func", func)
        return func

    def read_data_definition(self):
        """ Read a data definition. """
        ref = self.read_space_ref("memory")
        offset = self.read_expression()
        data = self.read_length_prefixed_bytes()
        return components.Data(ref, offset, data)

    def read_custom_definition(self):
        """ Read a custom definition. """
        name = self.read_str()
        data = self.read_exactly()
        return components.Custom(name, data)


# This is a list of functions to read specific argument types:
rfm = {
    ArgType.TYPE: lambda reader: reader.read_type(),
    ArgType.U32: lambda reader: reader.read_uint(),
    ArgType.LABELIDX: lambda reader: reader.read_space_ref("label"),
    ArgType.LOCALIDX: lambda reader: reader.read_space_ref("local"),
    ArgType.GLOBALIDX: lambda reader: reader.read_space_ref("global"),
    ArgType.FUNCIDX: lambda reader: reader.read_space_ref("func"),
    ArgType.TYPEIDX: lambda reader: reader.read_space_ref("type"),
    ArgType.TABLEIDX: lambda reader: reader.read_space_ref("table"),
    ArgType.I32: lambda reader: reader.read_int(),
    ArgType.I64: lambda reader: reader.read_int(),
    ArgType.F32: lambda reader: reader.read_f32(),
    ArgType.F64: lambda reader: reader.read_f64(),
}
