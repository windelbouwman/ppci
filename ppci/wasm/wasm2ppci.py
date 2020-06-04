""" Convert Web Assembly (WASM) into PPCI IR. """

import logging
import struct
from .. import ir
from .. import irutils
from .. import common
from ..binutils import debuginfo
from ..arch.arch_info import TypeInfo
from . import components
from .opcodes import STORE_OPS, LOAD_OPS, BINOPS, CMPOPS, STACK_IO
from .util import sanitize_name


def wasm_to_ir(
    wasm_module: components.Module, ptr_info, reporter=None
) -> ir.Module:
    """ Convert a WASM module into a PPCI native module.

    Args:
        wasm_module (ppci.wasm.Module): The wasm-module to compile
        ptr_info: :class:`ppci.arch.arch_info.TypeInfo` size and
                  alignment information for pointers.

    Returns:
        An IR-module.
    """
    compiler = WasmToIrCompiler(ptr_info)
    ppci_module = compiler.generate(wasm_module)
    if reporter:
        reporter.dump_ir(ppci_module)
    return ppci_module


class WasmToIrCompiler:
    """ Convert WASM instructions into PPCI IR instructions.
    """

    logger = logging.getLogger("wasm2ir")
    verbose = False

    def __init__(self, ptr_info):
        self.builder = irutils.Builder()
        self.blocknr = 0
        if not isinstance(ptr_info, TypeInfo):
            raise TypeError("Expected ptr_info to be TypeInfo")
        self.ptr_info = ptr_info
        self._opcode_dispatch = {}
        self._fill_dispatch_table()

    def _fill_dispatch_table(self):
        """ Fill the table of what to do with each instruction. """
        for opcode in STORE_OPS:
            self._opcode_dispatch[opcode] = self.gen_store

        for opcode in LOAD_OPS:
            self._opcode_dispatch[opcode] = self.gen_load

        self._opcode_dispatch["local.set"] = self.gen_local_set
        self._opcode_dispatch["local.tee"] = self.gen_local_set
        self._opcode_dispatch["local.get"] = self.gen_local_get
        self._opcode_dispatch["global.get"] = self.gen_global_get
        self._opcode_dispatch["global.set"] = self.gen_global_set

        for opcode in BINOPS:
            self._opcode_dispatch[opcode] = self.gen_binop

        for opcode in CMPOPS:
            self._opcode_dispatch[opcode] = self.gen_cmpop

        for opcode in [
            "f64.sqrt",
            "f64.abs",
            "f64.ceil",
            "f64.trunc",
            "f64.nearest",
            "f64.min",
            "f64.max",
            "f64.copysign",
            "f32.sqrt",
            "f32.abs",
            "f32.ceil",
            "f32.trunc",
            "f32.nearest",
            "f32.min",
            "f32.max",
            "f32.copysign",
            "f32.reinterpret_i32",
            "i64.clz",
            "i64.ctz",
            "i64.popcnt",
            "i64.rotl",
            "i64.rotr",
            "f64.reinterpret_i64",
            "i64.reinterpret_f64",
            "i32.reinterpret_f32",
            "i32.clz",
            "i32.ctz",
            "i32.popcnt",
            "i32.rotl",
            "i32.rotr",
            "memory.grow",
            "memory.size",
            "i32.extend8_s",
            "i32.extend16_s",
            "i64.extend8_s",
            "i64.extend16_s",
            "i64.extend32_s",
        ]:
            self._opcode_dispatch[opcode] = self.gen_instruction_fallback

        for opcode in ["f64.const", "f32.const", "i64.const", "i32.const"]:
            self._opcode_dispatch[opcode] = self.gen_const_instruction

        for opcode in ["f64.floor", "f32.floor"]:
            self._opcode_dispatch[opcode] = self.gen_floor_instruction

        for opcode in ["f64.neg", "f32.neg"]:
            self._opcode_dispatch[opcode] = self.gen_neg_instruction

        for opcode in [
            "i32.trunc_f32_s",
            "i32.trunc_f32_u",
            "i32.trunc_f64_s",
            "i32.trunc_f64_u",
            "i64.trunc_f32_s",
            "i64.trunc_f32_u",
            "i64.trunc_f64_s",
            "i64.trunc_f64_u",
        ]:
            self._opcode_dispatch[opcode] = self.gen_trunc_instruction

        for opcode in [
            "i32.trunc_sat_f32_s",
            "i32.trunc_sat_f32_u",
            "i32.trunc_sat_f64_s",
            "i32.trunc_sat_f64_u",
            "i64.trunc_sat_f32_s",
            "i64.trunc_sat_f32_u",
            "i64.trunc_sat_f64_s",
            "i64.trunc_sat_f64_u",
        ]:
            self._opcode_dispatch[
                opcode
            ] = self.gen_saturated_trunc_instruction

        self._opcode_dispatch["br"] = self.gen_br_instruction
        self._opcode_dispatch["br_if"] = self.gen_br_if_instruction
        self._opcode_dispatch["br_table"] = self.gen_br_table_instruction
        self._opcode_dispatch["call"] = self.gen_call_instruction
        self._opcode_dispatch[
            "call_indirect"
        ] = self.gen_call_indirect_instruction
        self._opcode_dispatch["return"] = self.gen_return_instruction
        self._opcode_dispatch["select"] = self.gen_select_instruction

        for opcode in [
            "i32.wrap_i64",
            "i64.extend_i32_s",
            "i64.extend_i32_u",
            "f64.convert_i32_s",
            "f64.convert_i32_u",
            "f64.convert_i64_s",
            "f64.convert_i64_u",
            "f32.convert_i32_s",
            "f32.convert_i32_u",
            "f32.convert_i64_s",
            "f32.convert_i64_u",
        ]:
            self._opcode_dispatch[opcode] = self.gen_convert_instruction

        for opcode in ["f64.promote_f32", "f32.demote_f64"]:
            self._opcode_dispatch[opcode] = self.gen_promote_instruction

    def generate(self, wasm_module: components.Module):
        assert isinstance(wasm_module, components.Module)

        # Create module:
        self.debug_db = debuginfo.DebugDb()
        self.builder.module = ir.Module("mainmodule", debug_db=self.debug_db)

        # First read all sections:
        # for wasm_function in wasm_module.sections[-1].functiondefs:
        self.wasm_types = []  # List[wasm.Type] (signature)
        self.globalz = []  # id -> (type, ir.Variable)
        self.gen_functions = []
        self.functions = []  # List of ir-function wasm signature pairs
        self._runtime_functions = {}  # Function required during runtime
        self.export_names = {}  # mapping of id's to exported function names
        self.start_function_ref = None
        self.tables = []  # Function pointer tables
        self.global_inits = (
            []
        )  # List of global variable initialization expressions

        self.memory_base_address = None

        for definition in wasm_module:
            self.gen_definition(definition)

        # Generate functions:
        for ppci_function, signature, wasm_function in self.gen_functions:
            self.generate_function(ppci_function, signature, wasm_function)

        # Generate run_init function:
        self.gen_init_procedure()

        function_names = [f[0].name for f in self.functions]
        global_names = [g for g in self.globalz]

        # TODO: hack to pass this information alongside module
        self.builder.module._wasm_function_names = function_names
        self.builder.module._wasm_global_names = global_names

        return self.builder.module

    def gen_definition(self, definition):
        """ Generate code for a single wasm definition. """
        if isinstance(definition, components.Type):
            # assert len(self.wasm_types) == definition.id
            self.wasm_types.append(definition)

        elif isinstance(definition, components.Import):
            self.gen_import_definition(definition)

        elif isinstance(definition, components.Export):
            self.gen_export_definition(definition)

        elif isinstance(definition, components.Start):
            # Generate a procedure which calls the start procedure:
            self.start_function_ref = definition.ref

        elif isinstance(definition, components.Func):
            self.gen_func_definition(definition)

        elif isinstance(definition, components.Table):
            self.gen_table_definition(definition)

        elif isinstance(definition, components.Elem):
            self.gen_elem_definition(definition)

        elif isinstance(definition, components.Global):
            self.gen_global_definition(definition)

        elif isinstance(definition, components.Memory):
            self.gen_memory_definition(definition)

        elif isinstance(definition, components.Data):
            # Data is intended for the runtime to handle.
            pass

        elif isinstance(definition, components.Custom):
            pass

        else:  # pragma: no cover
            self.logger.error(
                "Definition %s not implemented", definition.__name__
            )
            raise NotImplementedError(definition.__name__)

    def gen_import_definition(self, definition):
        """ Generate code for import """
        # name = definition.name
        if definition.kind == "func":
            # index = definition.id
            sig = self.wasm_types[definition.info[0].index]
            name = "{}_{}".format(definition.modname, definition.name)
            arg_types = [self.get_ir_type(p[1]) for p in sig.params]

            if sig.results:
                if len(sig.results) == 1:
                    ret_type = self.get_ir_type(sig.results[0])
                    extern_ir_function = ir.ExternalFunction(
                        name, arg_types, ret_type
                    )
                else:
                    raise ValueError(
                        "Cannot handle {} return values".format(
                            len(sig.results)
                        )
                    )
            else:
                extern_ir_function = ir.ExternalProcedure(name, arg_types)

            self.logger.debug(
                "Creating external %s with signature %s",
                extern_ir_function,
                sig.to_string(),
            )
            self.builder.module.add_external(extern_ir_function)
            self.functions.append((extern_ir_function, sig))
        elif definition.kind == "memory":
            assert self.memory_base_address is None
            self.memory_base_address = ir.ExternalVariable("wasm_mem0_address")
            self.builder.module.add_external(self.memory_base_address)

        elif definition.kind == "table":
            assert not hasattr(self, "table_var")
            self.logger.debug("table import")
            assert definition.info[0] == "funcref"
            self.table_var = ir.ExternalVariable("func_table")
            self.builder.module.add_external(self.table_var)
            self.tables.append((self.table_var, []))
        elif definition.kind == "global":
            self.logger.debug("global import")
            # TODO: think of nicer names:
            global_var = ir.ExternalVariable("global0")
            self.builder.module.add_external(global_var)
            ir_typ = self.get_ir_type(definition.info[0])
            self.globalz.append((ir_typ, global_var))
        else:
            raise NotImplementedError(definition.kind)

    def gen_export_definition(self, definition):
        """ Generate code for an export definition. """
        name = sanitize_name(definition.name)

        if definition.kind == "func":
            # f = self.function_space[x.index]
            # f = x.name, f[1]
            if definition.ref.name is not None:
                # We can export a function multiple times with the
                # same name!
                # assert definition.ref.name not in export_names
                self.export_names[definition.ref.name] = name

            if definition.ref.index is not None:
                if definition.ref.index in self.export_names:
                    self.logger.debug(
                        "Exporting function twice, now with name %s", name,
                    )
                else:
                    self.export_names[definition.ref.index] = name
        else:
            pass
            # raise NotImplementedError(x.kind)

    def gen_func_definition(self, definition):
        """ Generate function definition. """
        signature = self.wasm_types[definition.ref.index]
        # Set name of function. If we have a string id prefer that,
        # otherwise we may have a name from import/export,
        # otherwise use index
        if definition.id in self.export_names:
            name = self.export_names[definition.id]
        elif isinstance(definition.id, str):
            name = "named_{}".format(sanitize_name(definition.id.lstrip("$")))
        else:
            name = "_unnamed_{}".format(definition.id)

        # Create ir-function:
        binding = ir.Binding.GLOBAL
        if signature.results:
            if len(signature.results) == 1:
                ret_type = self.get_ir_type(signature.results[0])
                ppci_function = self.builder.new_function(
                    name, binding, ret_type
                )
            else:
                # Create a procedure which takes an additional
                # pointer to a return value data area
                ppci_function = self.builder.new_procedure(name, binding)
        else:
            ppci_function = self.builder.new_procedure(name, binding)

        self.functions.append((ppci_function, signature))
        self.gen_functions.append((ppci_function, signature, definition))

    def gen_table_definition(self, definition):
        """ Create room for a table of function pointers. """
        assert not hasattr(self, "table_var")

        if definition.kind != "funcref":
            raise NotImplementedError("Non function pointer tables")

        if definition.max is not None:
            max_size = max(definition.min, definition.max)
        else:
            max_size = definition.min

        size = max_size * self.ptr_info.size
        assert size >= 0
        if size == 0:
            # TODO: is this a hack?
            # What does it mean to have a table with no entries?
            # Reserve at least a single memory location.
            size = self.ptr_info.size

        self.table_var = ir.Variable(
            "func_table", ir.Binding.GLOBAL, size, self.ptr_info.alignment,
        )
        self.builder.module.add_variable(self.table_var)
        self.tables.append((self.table_var, []))

    def gen_elem_definition(self, definition):
        offset = definition.offset
        # TODO: what to do when offset is non-negative?
        # assert offset == 0
        refs = definition.refs
        self.tables[0][1].append((offset, refs))

    def gen_global_definition(self, definition):
        """ Generate room for a global variable. """
        ir_typ = self.get_ir_type(definition.typ)
        fmts = {ir.i32: "<i", ir.i64: "<q", ir.f32: "f", ir.f64: "d"}
        fmt = fmts[ir_typ]
        size = struct.calcsize(fmt)
        # assume init is (f64.const xx):
        # value = struct.pack(fmt, definition.init.args[0])
        name = "global_{}".format(str(definition.id).replace("$", "_"))
        binding = ir.Binding.GLOBAL
        g2 = ir.Variable(name, binding, size, size)
        self.builder.module.add_variable(g2)
        self.globalz.append((ir_typ, g2))
        self.global_inits.append((g2, definition.init))

        # Enter correct debug info:
        dbg_typ = self.get_debug_type(definition.typ)
        db_variable_info = debuginfo.DebugVariable(
            g2.name, dbg_typ, common.SourceLocation("main.wasm", 1, 1, 1),
        )
        self.debug_db.enter(g2, db_variable_info)

    def gen_memory_definition(self, definition):
        # Create a global pointer to the memory base address:
        assert self.memory_base_address is None
        self.memory_base_address = ir.Variable(
            "wasm_mem0_address",
            ir.Binding.GLOBAL,
            self.ptr_info.size,
            self.ptr_info.alignment,
        )
        self.builder.module.add_variable(self.memory_base_address)

    def gen_init_procedure(self):
        """ Generate an initialization procedure.

        - Initializes eventual function tables.
        - Calls an optionalstart procedure.
        """
        ppci_function = self.builder.new_procedure(
            "_run_init", ir.Binding.GLOBAL
        )
        self.builder.set_function(ppci_function)
        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        self.gen_init_globals()
        self.gen_init_tables()

        # Call optional start function:
        if self.start_function_ref is not None:
            target, _ = self.functions[self.start_function_ref.index]
            self.emit(ir.ProcedureCall(target, []))

        self.emit(ir.Exit())

        # Enter correct debug info:
        dbg_arg_types = []
        dbg_return_type = self.get_debug_type("void")
        db_function_info = debuginfo.DebugFunction(
            ppci_function.name,
            common.SourceLocation("main.wasm", 1, 1, 1),
            dbg_return_type,
            dbg_arg_types,
        )
        self.debug_db.enter(ppci_function, db_function_info)

    def gen_init_globals(self):
        # Initialize global values:
        # (This must be done here, since initial values may contain
        # imported globals)
        for g2, init in self.global_inits:
            value = self.gen_expression(init)
            self.emit(ir.Store(value, g2))

    def gen_init_tables(self):
        """ Initialization function to fill table with elements.
        """
        # Fill function pointer tables:
        # TODO: we might be able to do this at link time?
        for table_variable, elems in self.tables:
            # TODO: what if alignment is bigger than size?
            assert self.ptr_info.size == self.ptr_info.alignment
            ptr_size = self.emit(
                ir.Const(self.ptr_info.size, "ptr_size", ir.ptr)
            )

            # Loop over elems which initialize table:
            for offset, functions in elems:
                # Start at the bottom of the variable table:
                address = table_variable

                # Add offset:
                offset_value = self.gen_expression(offset)
                assert offset_value.ty is ir.i32
                offset_value = self.emit(
                    ir.Cast(offset_value, "offset", ir.ptr)
                )
                offset_value = self.emit(
                    ir.mul(offset_value, ptr_size, "offset", ir.ptr)
                )
                address = self.emit(
                    ir.add(address, offset_value, "table_address", ir.ptr)
                )

                for func in functions:
                    # Lookup function
                    value = self.functions[func.index][0]
                    self.emit(ir.Store(value, address))
                    address = self.emit(
                        ir.add(address, ptr_size, "table_address", ir.ptr)
                    )

    def emit(self, ppci_inst):
        """ Emits the given instruction to the builder.
        """
        self.builder.emit(ppci_inst)
        return ppci_inst

    def new_block(self):
        self.blocknr += 1
        block_name = self.builder.function.name + "_block" + str(self.blocknr)
        self.logger.debug("creating block %s", block_name)
        return self.builder.new_block(block_name)

    TYP_MAP = {"i32": ir.i32, "i64": ir.i64, "f32": ir.f32, "f64": ir.f64}

    def get_ir_type(self, wasm_type):
        wasm_type = wasm_type.split(".")[0]
        return self.TYP_MAP[wasm_type]

    def get_debug_type(self, name):
        if self.debug_db.contains(name):
            return self.debug_db.get(name)
        else:
            dbg_type_map = {
                "f32": debuginfo.DebugBaseType("float", 4, 1),
                "f64": debuginfo.DebugBaseType("double", 8, 1),
                "i32": debuginfo.DebugBaseType("int", 4, 1),
                "i64": debuginfo.DebugBaseType("long", 8, 1),
                "void": debuginfo.DebugBaseType("void", 0, 1),
            }
            dbg_typ = dbg_type_map[name]
            self.debug_db.enter(name, dbg_typ)
            return dbg_typ

    def gen_expression(self, expression):
        self.stack = []
        for instruction in expression:
            self.generate_instruction(instruction)
        assert len(self.stack) == 1
        return self.stack[-1]

    def generate_function(self, ppci_function, signature, wasm_function):
        """ Generate code for a single function """
        self.logger.info(
            "Generating wasm function %s %s",
            ppci_function.name,
            signature.to_string(),
        )
        self.stack = []
        self.block_stack = []

        # Create correct debug signature for function:

        if signature.results and len(signature.results) == 1:
            dbg_return_type = self.get_debug_type(signature.results[0])
        else:
            dbg_return_type = self.get_debug_type("void")
        self.builder.set_function(ppci_function)

        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        dbg_arg_types = []
        self.locals = []  # todo: ak: why store on self?

        # First locals are the function arguments:
        for i, a_typ in enumerate(signature.params):
            ir_typ = self.get_ir_type(a_typ[1])
            ir_arg = ir.Parameter("param{}".format(i), ir_typ)
            dbg_arg_types.append(
                debuginfo.DebugParameter(
                    "arg{}".format(i), self.get_debug_type(a_typ[1])
                )
            )
            ppci_function.add_parameter(ir_arg)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc("alloc{}".format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, "local{}".format(i)))
            self.locals.append((ir_typ, addr))
            # Store parameter into local variable:
            self.emit(ir.Store(ir_arg, addr))

        # Insert multiple return values data area pointer:
        if signature.results and len(signature.results) > 1:
            multiple_return_data_ptr = ir.Parameter(
                "multiple_return_ptr", ir.ptr
            )
            ppci_function.add_parameter(multiple_return_data_ptr)
            dbg_void_ptr = debuginfo.DebugPointerType(
                self.get_debug_type("void")
            )
            dbg_arg_types.append(
                debuginfo.DebugParameter("multi_return_ptr", dbg_void_ptr)
            )

        # Enter correct debug info:
        db_function_info = debuginfo.DebugFunction(
            ppci_function.name,
            common.SourceLocation("main.wasm", 1, 1, 1),
            dbg_return_type,
            dbg_arg_types,
        )
        self.debug_db.enter(ppci_function, db_function_info)

        # Next are the rest of the locals:
        for i, local in enumerate(wasm_function.locals, len(self.locals)):
            local_id, local_typ = local
            local_id = i if local_id is None else local_id
            ir_typ = self.get_ir_type(local_typ)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc("alloc{}".format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, "local{}".format(i)))

            # Initialize local variable to zero:
            zero_init = self.emit(ir.Const(0, "local_init", ir_typ))
            self.emit(ir.Store(zero_init, addr))

            self.locals.append((ir_typ, addr))

        # Create an implicit top level block:
        final_phis = []
        for i, result in enumerate(signature.results):
            ir_typ = self.get_ir_type(result)
            final_phi = ir.Phi("function_result_{}".format(i), ir_typ)
            final_phis.append(final_phi)
        body_block = self.new_block()
        final_block = self.new_block()
        self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.block_stack.append(
            BlockLevel("block", final_block, body_block, [], final_phis, 0)
        )

        # Generate code for each instruction:
        num = len(wasm_function.instructions)
        for nr, instruction in enumerate(wasm_function.instructions, start=1):
            if self.verbose:
                self.logger.debug(
                    "%s/%s %s [stack=%s]",
                    nr,
                    num,
                    instruction.to_string(),
                    len(self.stack),
                )
            self.generate_instruction(instruction)

        # Close of function:
        self.fill_phis(final_phis)

        self.block_stack.pop()
        assert not self.block_stack

        if self.is_reachable:
            self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)
        if len(final_phis) == 0:
            assert isinstance(ppci_function, ir.Procedure)
            self.emit(ir.Exit())
        elif len(final_phis) == 1:
            # Single return value:
            assert isinstance(ppci_function, ir.Function)
            final_phi = final_phis[0]
            self.emit(final_phi)
            self.emit(ir.Return(final_phi))
        else:
            # multiple return values!
            # Store values in memory slab pointer provided by caller.
            assert len(final_phis) > 1
            assert isinstance(ppci_function, ir.Procedure)

            # TODO: use 8 as increment, to play safe
            # but we could be more efficient here.
            inc = self.emit(ir.Const(8, "inc", ir.ptr))
            for final_phi in final_phis:
                self.emit(final_phi)
                # Store value:
                self.emit(ir.Store(final_phi, multiple_return_data_ptr))
                multiple_return_data_ptr = self.emit(
                    ir.add(multiple_return_data_ptr, inc, "new_ptr", ir.ptr)
                )

            self.emit(ir.Exit())

        # Sometimes this assert throws:
        # TODO: enable the below assert:
        # assert not self.stack

        ppci_function.delete_unreachable()

    OPMAP = dict(
        eqz="==",
        eq="==",
        ne="!=",
        ge=">=",
        ge_u=">=",
        ge_s=">=",
        le="<=",
        le_u="<=",
        le_s="<=",
        gt=">",
        gt_u=">",
        gt_s=">",
        lt="<",
        lt_u="<",
        lt_s="<",
    )

    def get_block_signature(self, instruction):
        block_type = instruction.args[0]
        if block_type == "emptyblock":
            param_types = []
            result_types = []
        elif isinstance(block_type, str):
            param_types = []
            result_types = [block_type]
        else:
            type_id = block_type.index
            signature = self.wasm_types[type_id]
            param_types = [p[1] for p in signature.params]
            result_types = signature.results
        return param_types, result_types

    def get_phis(self, instruction):
        """ Get phi instructions for the given loop/block/if. """
        param_types, result_types = self.get_block_signature(instruction)

        param_phis = [
            ir.Phi("block_param_{}".format(nr), self.get_ir_type(param_type))
            for nr, param_type in enumerate(param_types)
        ]

        result_phis = [
            ir.Phi("block_result_{}".format(nr), self.get_ir_type(result_type))
            for nr, result_type in enumerate(result_types)
        ]
        return param_phis, result_phis

    def fill_phis(self, phis):
        """ Fill phis with current stack top. """
        if phis and self.is_reachable:
            # Step 1: gather values required:
            values = [self.pop_value(ir_typ=phi.ty) for phi in reversed(phis)]
            values.reverse()

            # Step 2: fill phis:
            incoming_block = self.builder.block
            assert incoming_block is not None
            for phi, value in zip(phis, values):
                self.logger.debug("Filling phi %s", phi)
                phi.set_incoming(incoming_block, value)

            # Step 3: Restore the stack:
            for value in values:
                self.push_value(value)

    def pop_block(self):
        """ Pop a control block of the block stack.
        """
        block = self.block_stack[-1]
        self.fill_phis(block.result_phis)

        self.block_stack.pop()
        # The value stack may contain more items, clear them off
        self.unwind(block)
        return block

    def pop_condition(self):
        """ Get comparison, a and b of the value stack """
        if len(self.stack) > self.block_stack[-1].stack_start:
            value = self.stack.pop()
            if isinstance(value, ir.Value):
                assert value.ty is ir.i32
                a = value
                b = self.emit(ir.Const(0, "zero", ir.i32))
                return "!=", a, b
            else:
                return value
        else:
            raise ValueError("Value stack underflow")

    def pop_value(self, ir_typ=None):
        """ Pop a value of the stack """
        if len(self.stack) > self.block_stack[-1].stack_start:
            value = self.stack.pop()
            if isinstance(value, ir.Value):
                pass
            else:
                #
                op, a, b = value
                value = self.emit_condition_to_value(op, a, b)

            if ir_typ:
                assert value.ty is ir_typ
            return value
        else:
            raise ValueError("Value stack underflow")

    def emit_condition_to_value(self, op, a, b):
        """ Emit some sort of weird ternary operation.

        Turn two values and a condition into 1 or 0.
        """
        ja = self.builder.new_block()
        nein = self.builder.new_block()
        immer = self.builder.new_block()
        self.emit(ir.CJump(a, op, b, ja, nein))

        self.builder.set_block(ja)
        one = self.emit(ir.Const(1, "one", ir.i32))
        self.emit(ir.Jump(immer))

        self.builder.set_block(nein)
        zero = self.emit(ir.Const(0, "zero", ir.i32))
        self.emit(ir.Jump(immer))

        self.builder.set_block(immer)
        phi = ir.Phi("ternary", ir.i32)
        phi.set_incoming(ja, one)
        phi.set_incoming(nein, zero)
        self.emit(phi)
        return phi

    def push_value(self, value):
        """ Put a value on top of the stack """
        self.stack.append(value)

    def unwind(self, block):
        """ Unwind the value stack """
        while len(self.stack) > block.stack_start:
            self.stack.pop()

    def generate_instruction(self, instruction):
        """ Generate ir-code for a single wasm instruction """
        opcode = instruction.opcode

        # IMPORTANT: handle block instructions first
        # Then check if we are in unreachable code, and do not generate
        # instructions in the unreachable space:
        if opcode == "block":
            self.gen_block_instruction(instruction)

        elif opcode == "loop":
            self.gen_loop_instruction(instruction)

        elif opcode == "if":
            self.gen_if_instruction(instruction)

        elif opcode == "else":
            self.gen_else_instruction()

        elif opcode == "end":
            self.gen_end_instruction()

        elif not self.is_reachable:
            # This is a guarding condition for the other instructions
            pass

        elif opcode in self._opcode_dispatch:
            self._opcode_dispatch[opcode](instruction)

        elif opcode == "unreachable":
            self.gen_unreachable_instruction()

        elif opcode == "drop":
            # Drop value on the stack
            self.pop_value()

        elif opcode == "nop":
            pass  # Easy money :D

        else:  # pragma: no cover
            raise NotImplementedError(opcode)

    def gen_promote_instruction(self, instruction):
        """ Generate code for promote / demote. """
        opcode = instruction.opcode
        # TODO: in theory this should be solvable in ir-code.
        if True:
            self._runtime_call(opcode)
        else:
            from_ir_typ = self.get_ir_type(opcode.split("_")[1])
            ir_typ = self.get_ir_type(opcode.split(".")[0])
            value = self.pop_value(ir_typ=from_ir_typ)
            value = self.emit(ir.Cast(value, "cast", ir_typ))
            self.push_value(value)

    def gen_convert_instruction(self, instruction):
        opcode = instruction.opcode
        from_typ = opcode.split("_")[1]
        from_ir_typ = self.get_ir_type(from_typ)
        ir_typ = self.get_ir_type(opcode.split(".")[0])
        value = self.pop_value(ir_typ=from_ir_typ)
        if "_u" in opcode:
            # First cast to unsigned value:
            mp = {"i32": ir.u32, "i64": ir.u64}
            unsigned_ir_typ = mp[from_typ]
            value = self.emit(ir.Cast(value, "unsigned", unsigned_ir_typ))
        value = self.emit(ir.Cast(value, "cast", ir_typ))
        self.push_value(value)

    def gen_trunc_instruction(self, instruction):
        """ Generate code for iNN.trunc_fMM_X.

        For example: i64.trunc_f32_u
        """
        # TODO: in theory this should be solvable in ir-code.
        opcode = instruction.opcode
        if True:
            self._runtime_call(opcode)
        else:
            from_typ = opcode.split("_")[1]
            from_ir_typ = self.get_ir_type(from_typ)
            ir_typ = self.get_ir_type(opcode.split(".")[0])
            value = self.pop_value(ir_typ=from_ir_typ)
            if "_u" in opcode:
                # First cast to unsigned value:
                mp = {"i32.trunc_u": ir.u32, "i64.trunc_u": ir.u64}
                unsigned_ir_typ = mp[opcode.split("/")[0]]
                value = self.emit(ir.Cast(value, "unsigned", unsigned_ir_typ))
            value = self.emit(ir.Cast(value, "cast", ir_typ))
            self.push_value(value)

    def gen_saturated_trunc_instruction(self, instruction):
        """ Generate code for iNN.trunc_sat_fMM_X.

        For example: i64.trunc_f32_u
        """
        # TODO: in theory this should be solvable in ir-code.
        opcode = instruction.opcode
        self._runtime_call(opcode)

    def gen_const_instruction(self, instruction):
        """ Generate code for i32.const and friends. """
        opcode = instruction.opcode
        value = self.emit(
            ir.Const(instruction.args[0], "const", self.get_ir_type(opcode))
        )
        self.push_value(value)

    def gen_local_set(self, instruction):
        opcode = instruction.opcode
        ty, local_var = self.locals[instruction.args[0].index]
        value = self.pop_value(ir_typ=ty)
        self.emit(ir.Store(value, local_var))
        if opcode == "local.tee":
            self.push_value(value)

    def gen_local_get(self, instruction):
        ty, local_var = self.locals[instruction.args[0].index]
        value = self.emit(ir.Load(local_var, "local_get", ty))
        self.push_value(value)

    def gen_global_get(self, instruction):
        ty, addr = self.globalz[instruction.args[0].index]
        value = self.emit(ir.Load(addr, "global_get", ty))
        self.push_value(value)

    def gen_global_set(self, instruction):
        ty, addr = self.globalz[instruction.args[0].index]
        value = self.pop_value(ir_typ=ty)
        self.emit(ir.Store(value, addr))

    def gen_floor_instruction(self, instruction):
        opcode = instruction.opcode
        self._runtime_call(opcode)

        # TODO: this does not work for all cases:
        # ir_typ = self.get_ir_type(opcode)
        # value = self.pop_value(ir_typ)
        # value = self.emit(ir.Cast(value, 'cast', ir.u64))
        # value = self.emit(ir.Cast(value, 'cast', ir_typ))
        # self.push_value(value)
        # Someday we may have a Unary op for this,
        # or a call into a native runtime lib?
        # value = self.emit(
        #     ir.Unop('floor', self.pop_value(ir_typ), 'floor', ir_typ))
        # self.push_value(value)

    def gen_neg_instruction(self, instruction):
        """ Generate code for (f32|f64).neg """
        ir_typ = self.get_ir_type(instruction.opcode)
        value = self.emit(ir.Unop("-", self.pop_value(ir_typ), "neg", ir_typ))
        self.push_value(value)

    def gen_binop(self, instruction):
        """ Generate code for binary operator """
        opcode = instruction.opcode
        itype, opname = opcode.split(".")
        op_map = {
            "add": "+",
            "sub": "-",
            "mul": "*",
            "div": "/",
            "div_s": "/",
            "div_u": "/",
            "rem_s": "%",
            "rem_u": "%",
            "and": "&",
            "or": "|",
            "xor": "^",
            "shl": "<<",
            "shr_u": ">>",
            "shr_s": ">>",
        }
        op = op_map[opname]
        name = "op_{}".format(opname)
        ir_typ = self.get_ir_type(itype)
        b = self.pop_value(ir_typ=ir_typ)
        a = self.pop_value(ir_typ=ir_typ)
        do_unsigned = "_u" in opname
        if do_unsigned:
            # Unsigned operation, first cast to unsigned:
            u_ir_typ = {ir.i32: ir.u32, ir.i64: ir.u64}[ir_typ]
            a = self.emit(ir.Cast(a, "cast", u_ir_typ))
            b = self.emit(ir.Cast(b, "cast", u_ir_typ))
            value = self.emit(ir.Binop(a, op, b, name, u_ir_typ))
            value = self.emit(ir.Cast(value, "cast", ir_typ))
        else:
            value = self.emit(ir.Binop(a, op, b, name, ir_typ))
        self.push_value(value)

    def gen_cmpop(self, instruction):
        """ Generate code for a comparison operation """
        opcode = instruction.opcode
        itype, opname = opcode.split(".")
        ir_typ = self.get_ir_type(itype)
        if opname in ["eqz"]:
            b = self.emit(ir.Const(0, "zero", ir_typ))
            a = self.pop_value(ir_typ=ir_typ)
        else:
            b = self.pop_value(ir_typ=ir_typ)
            a = self.pop_value(ir_typ=ir_typ)
        is_unsigned = "_u" in opcode
        if is_unsigned:
            # Cast to unsigned
            u_ir_typ = {ir.i32: ir.u32, ir.i64: ir.u64}[ir_typ]
            a = self.emit(ir.Cast(a, "cast", u_ir_typ))
            b = self.emit(ir.Cast(b, "cast", u_ir_typ))

        op = self.OPMAP[opname]
        self.push_value((op, a, b))
        # todo: hack; we assume this is the only test in an if

    def gen_load(self, instruction):
        """ Generate code for load instruction """
        itype, load_op = instruction.opcode.split(".")
        ir_typ = self.get_ir_type(itype)
        _, offset = instruction.args
        address = self.get_memory_address(offset)
        if load_op == "load":
            value = self.emit(ir.Load(address, "load", ir_typ))
        else:
            # Load different data-type and cast:
            load_ir_typ = {
                "load8_u": ir.u8,
                "load8_s": ir.i8,
                "load16_u": ir.u16,
                "load16_s": ir.i16,
                "load32_u": ir.u32,
                "load32_s": ir.i32,
            }[load_op]
            value = self.emit(ir.Load(address, "load", load_ir_typ))
            value = self.emit(ir.Cast(value, "casted_load", ir_typ))
        self.push_value(value)

    def gen_store(self, instruction):
        """ Generate code for store instruction """
        itype, store_op = instruction.opcode.split(".")
        ir_typ = self.get_ir_type(itype)
        # ACHTUNG: alignment and offset are swapped in text:
        _, offset = instruction.args
        value = self.pop_value(ir_typ=ir_typ)
        address = self.get_memory_address(offset)
        if store_op == "store":
            self.emit(ir.Store(value, address))
        else:
            store_ir_typ = {
                "store8": ir.i8,
                "store16": ir.i16,
                "store32": ir.i32,
            }[store_op]
            value = self.emit(ir.Cast(value, "casted_value", store_ir_typ))
            self.emit(ir.Store(value, address))

    def get_memory_address(self, offset):
        """ Emit code to retrieve a memory address """
        base = self.pop_value()
        if base.ty is not ir.ptr:
            base = self.emit(ir.Cast(base, "cast", ir.ptr))
        offset = self.emit(ir.Const(offset, "offset", ir.ptr))
        address = self.emit(ir.add(base, offset, "address", ir.ptr))
        mem0 = self.emit(ir.Load(self.memory_base_address, "mem0", ir.ptr))
        address = self.emit(ir.add(mem0, address, "address", ir.ptr))
        return address

    @property
    def is_reachable(self):
        """ Determine if the current position is reachable """
        # Attention:
        # Since block implements iter, one cannot check for bool(block) if
        # the block is empty.. So we have to check for None here:
        return self.builder.block is not None

    def gen_block_instruction(self, instruction):
        """ Generate start of block """
        stack_start = len(self.stack)
        if self.is_reachable:
            self.logger.debug("start of block")
            param_phis, result_phis = self.get_phis(instruction)
            inner_block = self.new_block()
            continue_block = self.new_block()
            self.fill_phis(param_phis)
            self.emit(ir.Jump(inner_block))
            self.builder.set_block(inner_block)
            for phi in param_phis:
                self.emit(phi)
                self.push_value(phi)
        else:
            self.logger.debug("start of unreachable block")
            param_phis = []
            result_phis = []
            inner_block = None
            continue_block = None

        self.block_stack.append(
            BlockLevel(
                "block",
                continue_block,
                inner_block,
                param_phis,
                result_phis,
                stack_start,
            )
        )

    def gen_loop_instruction(self, instruction):
        """ Generate code for a loop start """
        stack_start = len(self.stack)
        if self.is_reachable:
            param_phis, result_phis = self.get_phis(instruction)
            inner_block = self.new_block()
            continue_block = self.new_block()
            self.fill_phis(param_phis)
            self.emit(ir.Jump(inner_block))
            self.builder.set_block(inner_block)
            for phi in param_phis:
                self.emit(phi)
                self.push_value(phi)
        else:
            param_phis = []
            result_phis = None
            inner_block = None
            continue_block = None
        self.block_stack.append(
            BlockLevel(
                "loop",
                continue_block,
                inner_block,
                param_phis,
                result_phis,
                stack_start,
            )
        )

    def gen_end_instruction(self):
        """ Generate code for end instruction.

        This is a more or less complex task. It has to deal with unreachable
        code as well.
        """
        block = self.pop_block()

        # If we are not unreachable:
        if self.is_reachable:
            assert block.continue_block is not None
            self.emit(ir.Jump(block.continue_block))

        if block.typ == "if" and block.inner_block is not None:
            # We should connect empty else to end block.
            self.builder.set_block(block.inner_block)

            # Shortcut-circuit param arguments to result phis:
            assert len(block.param_phis) == len(block.result_phis)
            for param_value, result_phi in zip(
                block.param_phis, block.result_phis
            ):
                result_phi.set_incoming(block.inner_block, param_value)

            self.emit(ir.Jump(block.continue_block))

        self.builder.set_block(block.continue_block)

        # if we close a block that yields values
        # introduce a phi values for each created value.
        for phi in block.result_phis:
            self.logger.debug("Put %s on stack", phi)
            self.emit(phi)
            self.push_value(phi)

    def gen_if_instruction(self, instruction):
        """ Generate code for an if start """
        if self.is_reachable:
            # todo: we assume that the test is a comparison
            op, a, b = self.pop_condition()
            true_block = self.new_block()
            continue_block = self.new_block()
            else_block = self.new_block()
            stack_start = len(self.stack)

            param_phis, result_phis = self.get_phis(instruction)
            param_values = [
                self.pop_value(ir_typ=phi.ty) for phi in reversed(param_phis)
            ]
            param_values.reverse()
            # Restore stack:
            for value in param_values:
                self.push_value(value)

            # prepare values for then block:
            for param_value in param_values:
                self.push_value(param_value)

            self.emit(ir.CJump(a, op, b, true_block, else_block))
            self.builder.set_block(true_block)
        else:
            continue_block = None
            else_block = None
            param_values = []
            result_phis = []
            stack_start = len(self.stack)

        # Store else block as inner block to allow break:
        self.block_stack.append(
            BlockLevel(
                "if",
                continue_block,
                else_block,
                param_values,
                result_phis,
                stack_start,
            )
        )

    def gen_else_instruction(self):
        """ Generate code for else instruction """
        if_block = self.pop_block()
        assert if_block.typ == "if"

        # else_block was stored in inner block
        else_block = if_block.inner_block
        continue_block = if_block.continue_block

        for param_value in if_block.param_phis:
            self.push_value(param_value)

        if self.is_reachable:
            self.emit(ir.Jump(continue_block))
        self.builder.set_block(else_block)
        self.block_stack.append(
            BlockLevel(
                "else",
                continue_block,
                None,
                if_block.param_phis,
                if_block.result_phis,
                if_block.stack_start,
            )
        )

    def gen_call_instruction(self, instruction):
        """ Generate a function call """
        # Call another function!
        idx = instruction.args[0].index
        ir_function, signature = self.functions[idx]
        self._gen_call_helper(ir_function, signature)

    def gen_call_indirect_instruction(self, instruction):
        """ Call another function by pointer! """
        type_id = instruction.args[0].index
        signature = self.wasm_types[type_id]
        func_index = self.pop_value()
        ptr_size = self.emit(ir.Const(self.ptr_info.size, "ptr_size", ir.i32))
        element_offset = self.emit(
            ir.Cast(
                self.emit(
                    ir.mul(func_index, ptr_size, "element_offset", ir.i32)
                ),
                "element_offset",
                ir.ptr,
            )
        )
        element_address = self.emit(
            ir.add(self.table_var, element_offset, "element_address", ir.ptr)
        )
        func_ptr = self.emit(ir.Load(element_address, "func_ptr", ir.ptr))
        # TODO: how to check function type during runtime?

        self._gen_call_helper(func_ptr, signature)

    def _gen_call_helper(self, target, signature):
        """ Common function calling logic """
        self.logger.debug(
            "Calling function %s with signature %s",
            target,
            signature.to_string(),
        )

        args = [self.pop_value() for _ in range(len(signature.params))]
        # Note that the top of the stack contains the last argument:
        args.reverse()
        for arg, arg_type in zip(args, signature.params):
            ir_typ = self.get_ir_type(arg_type[1])
            assert arg.ty is ir_typ

        if signature.results:
            if len(signature.results) == 1:
                ir_typ = self.get_ir_type(signature.results[0])
                value = self.emit(
                    ir.FunctionCall(target, args, "call", ir_typ)
                )
                self.push_value(value)
            else:
                assert len(signature.results) > 1
                # allocate a memory slab, and inject a pointer to it as first argument.
                data_area_size = len(signature.results) * 8
                data_area_alignment = 8
                data_area = self.emit(
                    ir.Alloc(
                        "return_values_area",
                        data_area_size,
                        data_area_alignment,
                    )
                )
                multi_return_ptr = self.emit(
                    ir.AddressOf(data_area, "return_values_ptr")
                )
                args.append(multi_return_ptr)

                # Invoke function:
                self.emit(ir.ProcedureCall(target, args))

                # Unpack the multiple return values:
                inc = self.emit(ir.Const(8, "inc", ir.ptr))
                for nr, result in enumerate(signature.results):
                    ir_typ = self.get_ir_type(result)
                    value = self.emit(
                        ir.Load(
                            multi_return_ptr,
                            "return_value_{}".format(nr),
                            ir_typ,
                        )
                    )
                    self.push_value(value)
                    multi_return_ptr = self.emit(
                        ir.add(multi_return_ptr, inc, "inc", ir.ptr)
                    )

        else:
            self.emit(ir.ProcedureCall(target, args))

    def gen_select_instruction(self, instruction):
        """ Generate code for the select wasm instruction """
        # This is roughly equivalent to C-style: a ? b : c
        op, a, b = self.pop_condition()
        nein_value, ja_value = self.pop_value(), self.pop_value()

        ja_block = self.builder.new_block()
        nein_block = self.builder.new_block()
        immer = self.builder.new_block()
        self.emit(ir.CJump(a, op, b, ja_block, nein_block))

        self.builder.set_block(ja_block)
        self.emit(ir.Jump(immer))

        self.builder.set_block(nein_block)
        self.emit(ir.Jump(immer))

        self.builder.set_block(immer)
        phi = ir.Phi("ternary", ja_value.ty)
        phi.set_incoming(ja_block, ja_value)
        phi.set_incoming(nein_block, nein_value)
        self.emit(phi)
        self.push_value(phi)

    def gen_unreachable_instruction(self):
        """ Generate appropriate code for an unreachable instruction.

        What we will do, is we call an external function to handle this
        exception. Also we will return from the subroutine.
        """
        self._runtime_call("unreachable")
        if isinstance(self.builder.function, ir.Procedure):
            self.emit(ir.Exit())
        else:
            # TODO: massive hack just to return some value:
            # TODO: do we need ir.Unreachable()?
            v = self.emit(
                ir.Const(0, "unreachable", self.builder.function.return_ty)
            )
            self.emit(ir.Return(v))
        self.builder.set_block(None)

    def gen_instruction_fallback(self, instruction):
        opcode = instruction.opcode
        self._runtime_call(opcode)

    def gen_return_instruction(self, instruction):
        """ Generate code for return instruction.

        Treat return as a break to the top level block.
        """
        targetblock = self.block_stack[0].continue_block
        self.fill_phis(self.block_stack[0].result_phis)
        self.emit(ir.Jump(targetblock))
        self.builder.set_block(None)

    def gen_br_instruction(self, instruction):
        """ Generate code for br instruction """
        depth = instruction.args[0]
        targetblock = self.get_jump_target_block(depth)
        self.emit(ir.Jump(targetblock))
        self.builder.set_block(None)

    def gen_br_if_instruction(self, instruction):
        """ Generate code for br_if instruction """
        op, a, b = self.pop_condition()
        depth = instruction.args[0]
        targetblock = self.get_jump_target_block(depth)
        falseblock = self.new_block()
        self.emit(ir.CJump(a, op, b, targetblock, falseblock))
        self.builder.set_block(falseblock)

    def gen_br_table_instruction(self, instruction):
        """ Generate code for br_table instruction.
        This is a sort of switch case.

        This is called a jump table. Implement for now by chain of
        if else.
        """

        # TODO: when ir supports jump table, use it!
        test_value = self.pop_value()
        assert test_value.ty in [ir.i32, ir.i64]
        ir_typ = test_value.ty
        option_labels = instruction.args[0]
        default_label = option_labels.pop(-1)
        for i, option_label in enumerate(option_labels):
            # Figure which block we must jump to:
            depth = option_label
            target_block = self.get_jump_target_block(depth)
            ja_block = target_block
            nein_block = self.new_block()
            c = self.emit(ir.Const(i, "label", ir_typ))
            self.emit(ir.CJump(test_value, "==", c, ja_block, nein_block))
            self.builder.set_block(nein_block)

        # Determine default block:
        depth = default_label
        target_block = self.get_jump_target_block(depth)
        default_block = target_block
        self.emit(ir.Jump(default_block))
        self.builder.set_block(None)

    def get_jump_target_block(self, depth):
        """ Lookup the branch target and fill its optional value.
        """
        assert isinstance(depth, components.Ref)
        depth = depth.index
        block = self.block_stack[-depth - 1]
        if block.typ == "loop":
            self.fill_phis(block.param_phis)
            targetblock = block.inner_block
        else:
            self.fill_phis(block.result_phis)
            targetblock = block.continue_block
        return targetblock

    def _runtime_call(self, opcode):
        """ Generate runtime function call.

        This is required for functions such 'sqrt' as which do not have
        a reasonable ppci ir-code equivalent.
        """
        func_name = opcode.replace(".", "_")
        rt_func_name = "wasm_rt_" + func_name

        # Determine argument and return types:
        stack_in, stack_out = STACK_IO[opcode]
        arg_types = [self.get_ir_type(t) for t in stack_in]
        if stack_out:
            assert len(stack_out) == 1
            ir_typ = self.get_ir_type(stack_out[0])
        else:
            ir_typ = None

        # Get or create the runtime function:
        if rt_func_name in self._runtime_functions:
            rt_func = self._runtime_functions[rt_func_name]
        else:
            if ir_typ is None:
                rt_func = ir.ExternalProcedure(rt_func_name, arg_types)
            else:
                rt_func = ir.ExternalFunction(rt_func_name, arg_types, ir_typ)
            self._runtime_functions[rt_func_name] = rt_func
            self.builder.module.add_external(rt_func)

        # Grab arguments from stack:
        args = []
        for arg_ir_typ in reversed(arg_types):
            arg = self.pop_value(ir_typ=arg_ir_typ)
            args.append(arg)
        args.reverse()

        if ir_typ is None:
            value = self.emit(ir.ProcedureCall(rt_func, args))
        else:
            value = self.emit(
                ir.FunctionCall(rt_func, args, "rtlib_call_result", ir_typ)
            )
            self.push_value(value)


class BlockLevel:
    """ Store some info about blocks.

    Each block has optionally params and results.
    Both parameters and results are implemented as
    phi instructions.

    The output of a block can be reached in multiple ways.
    Likewise, the beginning of a block can also be reached
    in many ways.
    """

    def __init__(
        self,
        typ,
        continue_block,
        inner_block,
        param_phis,
        result_phis,
        stack_start,
    ):
        self.typ = typ
        self.continue_block = continue_block
        self.inner_block = inner_block
        self.param_phis = param_phis
        self.result_phis = result_phis
        self.stack_start = stack_start
