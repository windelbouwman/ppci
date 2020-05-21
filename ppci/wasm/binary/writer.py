""" Functionality to write a wasm module to its binary format.
"""


import logging
from io import BytesIO
from ...utils.leb128 import signed_leb128_encode, unsigned_leb128_encode
from ...format.io import BaseIoWriter
from ..opcodes import ArgType, OPERANDS, OPCODES
from ..components import Instruction, SECTION_IDS
from .. import components
from .io import LANG_TYPES


logger = logging.getLogger("wasm")


class BinaryFileWriter(BaseIoWriter):
    """ Write a wasm module as binary format. """

    def write_module(self, module):
        """ Write the given module as binary format. """
        self.write_header()

        # todo: allow custom section(s)
        # todo: WASM defines custom "name section": we can lookup names later!

        # Collect definitions, so we have the order right. The order is
        # probably already good because we read it as such, but better be safe.
        definitions = module.get_definitions_per_section()

        # Iterate over (possible) sections
        for section_name, section_id in SECTION_IDS.items():
            if section_name == "code":
                continue  # we have 'func' instead

            # Prepare file to write this section to.
            # It is tempting to use f.tell() and write the size later, but
            # these variable-sized ints make this difficult.
            f2 = BinaryFileWriter(BytesIO())

            if section_name == "function":
                if len(definitions["func"]) == 0:
                    continue

                # Special section that binds sigs to imports and implementation
                f2.write_vu32(len(definitions["func"]))
                for d in definitions["func"]:
                    f2.write_ref(d.ref)

            else:
                section_defs = definitions[section_name]
                if len(section_defs) == 0:
                    continue

                if section_name == "start":
                    assert len(section_defs) == 1, "Expected 0 or 1 start defs"
                    f2.write_definition(section_defs[0])
                elif section_name == "custom":
                    for d in section_defs:
                        f3 = BinaryFileWriter(BytesIO())
                        f3.write_definition(d)
                        payload = f3.f.getvalue()
                        #
                        f2.write_vu7(section_id)  # \x00
                        f2.write_vu32(len(payload))
                        f2.write(payload)
                else:
                    # Write how many definitions, and write each one
                    f2.write_vu32(len(section_defs))  # count
                    for index, d in enumerate(section_defs):
                        # Funcs need their param index/name space
                        # Note that id in Type.params can be int/str, not None
                        if section_name == "func":
                            typedefs = definitions["type"]
                            typedef = typedefs[d.ref.index]
                        # Write it!
                        f2.write_definition(d)

            # Write this section to our main file object
            payload = f2.f.getvalue()
            logger.debug(
                "Writing section %s of %s bytes" % (section_id, len(payload))
            )
            if section_name != "custom":
                self.write_vu7(section_id)
                self.write_vu32(len(payload))
            self.write(payload)

    def write_header(self):
        self.write(b"\x00asm")
        self.write_u32(1)  # version, must be 1 for now

    def write_definition(self, definition):
        """ Write a single definition.
        """
        mp = {
            components.Type: self.write_type_definition,
            components.Import: self.write_import_definition,
            components.Table: self.write_table_definition,
            components.Memory: self.write_memory_definition,
            components.Global: self.write_global_definition,
            components.Export: self.write_export_definition,
            components.Start: self.write_start_definition,
            components.Elem: self.write_elem_definition,
            components.Func: self.write_func_definition,
            components.Data: self.write_data_definition,
            components.Custom: self.write_custom_definition,
        }
        mp[type(definition)](definition)

    def write(self, bb):
        return self.f.write(bb)

    def write_f64(self, x):
        self.write_fmt("<d", x)

    def write_f32(self, x):
        self.write_fmt("<f", x)

    def write_u32(self, x):
        self.write_fmt("<I", x)

    def write_str(self, x):
        bb = x.encode("utf-8")
        self.write_vu32(len(bb))
        self.f.write(bb)

    def write_vs64(self, x):
        bb = signed_leb128_encode(x)
        if not len(bb) <= 10:
            raise ValueError("Cannot pack {} into 10 bytes".format(x))
        self.f.write(bb)

    def write_vs32(self, x):
        bb = signed_leb128_encode(x)
        if not len(bb) <= 5:  # 5 = ceil(32/7)
            raise ValueError("Cannot pack {} into 5 bytes".format(x))
        self.f.write(bb)

    def write_vu32(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) <= 5
        self.f.write(bb)

    def write_vu7(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) == 1
        self.f.write(bb)

    def write_vu1(self, x):
        bb = unsigned_leb128_encode(x)
        assert len(bb) == 1
        self.f.write(bb)

    def write_type(self, typ: str):
        """ Write type """
        self.write(LANG_TYPES[typ])

    def write_ref(self, ref):
        assert isinstance(ref, components.Ref)
        int_ref = ref.index
        self.write_vu32(int_ref)

    def write_limits(self, min, max):
        if max is None:
            self.write(b"\x00")
            self.write_vu32(min)
        else:
            self.write(b"\x01")
            self.write_vu32(min)
            self.write_vu32(max)

    def write_expression(self, expression):
        """ Write an expression (a list of instructions) """
        for instruction in expression:
            self.write_instruction(instruction)

        # Encode explicit end:
        self.write_instruction(Instruction("end"))

    def write_instruction(self, instruction):
        """ Write a single instruction as binary. """
        # Our instruction
        self.write(bytes([OPCODES[instruction.opcode]]))

        # Prep args for accessing named identifiers
        args = list(instruction.args)

        operands = OPERANDS[instruction.opcode]
        assert len(operands) == len(args)

        # Data comes after
        for o, arg in zip(operands, args):
            if o in wfm:
                wfm[o](self, arg)
            elif o == "byte":
                self.write(bytes([arg]))
            elif o == "br_table":
                assert instruction.opcode == "br_table"
                self.write_vu32(len(arg) - 1)
                for x in arg:
                    self.write_ref(x)
            else:
                raise TypeError("Unknown instruction arg %r" % o)

    def write_type_definition(self, type_definition):
        """ Write out a `type` definition entry. """
        self.write(b"\x60")  # form
        self.write_vu32(len(type_definition.params))  # params
        for _, paramtype in type_definition.params:
            self.write_type(paramtype)
        self.write_vu1(len(type_definition.results))  # returns
        for rettype in type_definition.results:
            self.write_type(rettype)

    def write_import_definition(self, import_definition):
        """ Write an `import` definition entry. """
        self.write_str(import_definition.modname)
        self.write_str(import_definition.name)
        if import_definition.kind == "func":
            self.write(b"\x00")
            # type-index, not func-
            self.write_ref(import_definition.info[0])
        elif import_definition.kind == "table":
            self.write(b"\x01")
            table_kind, min, max = import_definition.info
            self.write_type(table_kind)  # always 0x70 funcref in v1
            self.write_limits(min, max)
        elif import_definition.kind == "memory":
            self.write(b"\x02")
            min, max = import_definition.info
            self.write_limits(min, max)
        elif import_definition.kind == "global":
            self.write(b"\x03")
            typ, mutable = import_definition.info
            self.write_type(typ)
            self.write(bytes([int(mutable)]))
        else:  # pragma: no cover
            raise NotImplementedError(import_definition.kind)

    def write_table_definition(self, table):
        """ Write out a `table` definition. """
        self.write_type(table.kind)  # always 0x70 funcref in v1
        self.write_limits(table.min, table.max)

    def write_memory_definition(self, memory_definition: components.Memory):
        self.write_limits(memory_definition.min, memory_definition.max)

    def write_global_definition(self, global_definition):
        """ Write a global definition. """
        self.write_type(global_definition.typ)
        self.write(bytes([int(global_definition.mutable)]))

        # Encode value as expression followed by end instruction
        self.write_expression(global_definition.init)

    def write_export_definition(self, export):
        """ Write out an export definition. """
        self.write_str(export.name)
        type_id = {"func": 0, "table": 1, "memory": 2, "global": 3}[
            export.kind
        ]
        self.write(bytes([type_id]))
        assert export.ref.space == export.kind
        self.write_ref(export.ref)

    def write_start_definition(self, start):
        """ Write out a start definition. """
        assert start.ref.space == "func"
        self.write_ref(start.ref)

    def write_elem_definition(self, elem):
        """ Write out an `elem` definition. """
        assert elem.ref.space == "table"
        self.write_ref(elem.ref)
        # Encode offset as expression followed by end instruction
        self.write_expression(elem.offset)
        # Encode as u32 length followed by func indices:
        self.write_vu32(len(elem.refs))
        for ref in elem.refs:
            assert ref.space == "func"
            self.write_ref(ref)

    def write_func_definition(self, func):
        """ Write out a function. """
        # You would expect the ref to be used here, but the WASM spec has a
        # separate function section for that. Not sure why.

        # Collect locals by type
        local_entries = []  # list of (count, type) tuples
        for loc_id, loc_type in func.locals:
            if local_entries and local_entries[-1][1] == loc_type:
                local_entries[-1] = local_entries[-1][0] + 1, loc_type
            else:
                local_entries.append((1, loc_type))

        f3 = BinaryFileWriter(BytesIO())
        # Number of local-entries in this func
        f3.write_vu32(len(local_entries))
        for count, loc_type in local_entries:
            f3.write_vu32(count)  # number of locals of this type
            f3.write_type(loc_type)

        # Instructions:
        for instruction in func.instructions:
            f3.write_instruction(instruction)
        f3.write(b"\x0b")  # end
        body = f3.f.getvalue()
        self.write_vu32(len(body))  # number of bytes in body
        self.write(body)

    def write_data_definition(self, data_definition):
        """ Write out a `data` definition. """
        assert data_definition.ref.space == "memory"
        self.write_ref(data_definition.ref)

        # Encode offset as expression followed by end instruction
        self.write_expression(data_definition.offset)

        # Encode as u32 length followed by data:
        self.write_vu32(len(data_definition.data))
        self.write(data_definition.data)

    def write_custom_definition(self, custom):
        self.write_str(custom.name)
        self.write(custom.data)


# This is a list of functions to write argument of different types:
wfm = {
    ArgType.TYPE: lambda writer, arg: writer.write_type(arg),
    ArgType.U32: lambda writer, arg: writer.write_vu32(arg),
    ArgType.LABELIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.LOCALIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.GLOBALIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.FUNCIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.TYPEIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.TABLEIDX: lambda writer, arg: writer.write_ref(arg),
    ArgType.I32: lambda writer, arg: writer.write_vs32(arg),
    ArgType.I64: lambda writer, arg: writer.write_vs64(arg),
    ArgType.F32: lambda writer, arg: writer.write_f32(arg),
    ArgType.F64: lambda writer, arg: writer.write_f64(arg),
}
