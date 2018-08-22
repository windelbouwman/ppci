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
        wasm_module: components.Module, ptr_info, reporter=None) -> ir.Module:
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


def create_memories(wasm_module):
    """ Create a memory slab for the given wasm module.

    This function is intended to be called from the wasm runtime support
    libraries.
    """
    memories = []
    initializations = []
    for definition in wasm_module:
        if isinstance(definition, components.Memory):
            min_size = definition.min
            memories.append(
                (bytearray(min_size * 65536), min_size, definition.max))
        elif isinstance(definition, components.Data):
            assert len(definition.offset) == 1
            assert definition.offset[0].opcode == 'i32.const'
            offset = definition.offset[0].args[0]
            memory_index = definition.ref.index
            assert isinstance(memory_index, int)
            data = definition.data
            initializations.append((memory_index, offset, data))

    # Initialize various parts:
    for memory_index, offset, data in initializations:
        memory = memories[memory_index]
        memory[0][offset:offset+len(data)] = data

    return memories


class WasmToIrCompiler:
    """ Convert WASM instructions into PPCI IR instructions.
    """
    logger = logging.getLogger('wasm2ir')
    verbose = True

    def __init__(self, ptr_info):
        self.builder = irutils.Builder()
        self.blocknr = 0
        if not isinstance(ptr_info, TypeInfo):
            raise TypeError('Expected ptr_info to be TypeInfo')
        self.ptr_info = ptr_info

    def generate(self, wasm_module: components.Module):
        assert isinstance(wasm_module, components.Module)

        # Create module:
        self.debug_db = debuginfo.DebugDb()
        self.builder.module = ir.Module('mainmodule', debug_db=self.debug_db)

        # First read all sections:
        # for wasm_function in wasm_module.sections[-1].functiondefs:
        self.wasm_types = []  # List[wasm.Type] (signature)
        self.globalz = []  # id -> (type, ir.Variable)
        gen_functions = []
        self.functions = []  # List of ir-function wasm signature pairs
        self._runtime_functions = {}  # Function required during runtime
        export_names = {}  # mapping of id's to exported function names
        start_function_id = None
        tables = []  # Function pointer tables
        global_inits = []  # List of global variable initialization expressions

        self.memory_base_address = None

        for definition in wasm_module:
            if isinstance(definition, components.Type):
                # assert len(self.wasm_types) == definition.id
                self.wasm_types.append(definition)

            elif isinstance(definition, components.Import):
                # name = definition.name
                if definition.kind == 'func':
                    # index = definition.id
                    sig = self.wasm_types[definition.info[0].index]
                    name = '{}_{}'.format(definition.modname, definition.name)
                    arg_types = [self.get_ir_type(p[1]) for p in sig.params]

                    if sig.result:
                        if len(sig.result) != 1:
                            raise ValueError(
                                'Cannot handle {} return values'.format(
                                    len(sig.result)))
                        ret_type = self.get_ir_type(sig.result[0])
                        extern_ir_function = ir.ExternalFunction(
                            name, arg_types, ret_type)
                    else:
                        extern_ir_function = ir.ExternalProcedure(
                            name, arg_types)

                    self.logger.debug(
                        'Creating external %s with signature %s',
                        extern_ir_function, sig.to_string())
                    self.builder.module.add_external(extern_ir_function)
                    self.functions.append((extern_ir_function, sig))
                elif definition.kind == 'memory':
                    assert self.memory_base_address is None
                    self.memory_base_address = ir.ExternalVariable(
                        'wasm_mem0_address')
                    self.builder.module.add_external(self.memory_base_address)

                elif definition.kind == 'table':
                    self.logger.debug('table import')
                    assert definition.info[0] == 'anyfunc'
                    assert definition.id == 0
                    self.table_var = ir.ExternalVariable(
                        'func_table')
                    self.builder.module.add_external(self.table_var)
                    tables.append((self.table_var, []))
                elif definition.kind == 'global':
                    self.logger.debug('global import')
                    # TODO: think of nicer names:
                    global_var = ir.ExternalVariable(
                        'global0')
                    self.builder.module.add_external(global_var)
                    ir_typ = self.get_ir_type(definition.info[0])
                    self.globalz.append((ir_typ, global_var))
                else:
                    raise NotImplementedError(definition.kind)

            elif isinstance(definition, components.Export):
                if definition.kind == 'func':
                    # print(x.index)
                    # f = self.function_space[x.index]
                    # f = x.name, f[1]
                    name = sanitize_name(definition.name)
                    if definition.ref.name is not None:
                        assert definition.ref.name not in export_names
                        export_names[definition.ref.name] = name

                    if definition.ref.index is not None:
                        if definition.ref.index in export_names:
                            self.logger.debug('Exporting function twice, now with name %s', name)
                        else:
                            export_names[definition.ref.index] = name
                else:
                    pass
                    # raise NotImplementedError(x.kind)

            elif isinstance(definition, components.Start):
                # Generate a procedure which calls the start procedure:
                start_function_id = definition.ref

            elif isinstance(definition, components.Func):
                signature = self.wasm_types[definition.ref.index]
                # Set name of function. If we have a string id prefer that,
                # otherwise we may have a name from import/export,
                # otherwise use index
                # print(export_names, definition.id)
                if definition.id in export_names:
                    name = export_names[definition.id]
                elif isinstance(definition.id, str):
                    name = 'named_{}'.format(
                        sanitize_name(definition.id.lstrip('$')))
                else:
                    name = 'unnamed{}'.format(definition.id)

                # Create ir-function:
                if signature.result:
                    if len(signature.result) != 1:
                        raise ValueError(
                            'Cannot handle {} return values'.format(
                                len(signature.result)))
                    ret_type = self.get_ir_type(signature.result[0])
                    ppci_function = self.builder.new_function(name, ret_type)
                else:
                    ppci_function = self.builder.new_procedure(name)

                self.functions.append((ppci_function, signature))
                gen_functions.append((ppci_function, signature, definition))

            elif isinstance(definition, components.Table):
                assert definition.id in (0, '$0')
                if definition.kind != 'anyfunc':
                    raise NotImplementedError('Non function pointer tables')
                if definition.max is not None:
                    max_size = max(definition.min, definition.max)
                else:
                    max_size = definition.min
                size = max_size * self.ptr_info.size
                self.table_var = ir.Variable(
                    'func_table', size, self.ptr_info.alignment)
                self.builder.module.add_variable(self.table_var)
                tables.append((self.table_var, []))

            elif isinstance(definition, components.Elem):
                offset = definition.offset
                # TODO: what to do when offset is non-negative?
                # assert offset == 0
                refs = definition.refs
                tables[0][1].append((offset, refs))

            elif isinstance(definition, components.Global):
                ir_typ = self.get_ir_type(definition.typ)
                fmts = {
                    ir.i32: '<i', ir.i64: '<q',
                    ir.f32: 'f', ir.f64: 'd',
                }
                fmt = fmts[ir_typ]
                size = struct.calcsize(fmt)
                # assume init is (f64.const xx):
                # value = struct.pack(fmt, definition.init.args[0])
                name = 'global_{}'.format(
                    str(definition.id).replace('$', '_'))
                g2 = ir.Variable(name, size, size)
                self.builder.module.add_variable(g2)
                self.globalz.append((ir_typ, g2))
                global_inits.append((g2, definition.init))

                # Enter correct debug info:
                dbg_typ = self.get_debug_type(definition.typ)
                db_variable_info = debuginfo.DebugVariable(
                    g2.name,
                    dbg_typ,
                    common.SourceLocation('main.wasm', 1, 1, 1)
                )
                self.debug_db.enter(g2, db_variable_info)

            elif isinstance(definition, components.Memory):
                # Create a global pointer to the memory base address:
                assert self.memory_base_address is None
                self.memory_base_address = ir.Variable(
                    'wasm_mem0_address', self.ptr_info.size,
                    self.ptr_info.alignment)
                self.builder.module.add_variable(self.memory_base_address)

            elif isinstance(definition, components.Data):
                # Data is intended for the runtime to handle.
                pass

            elif isinstance(definition, components.Custom):
                pass

            else:
                # todo: Table, Element, Memory, Data
                self.logger.error(
                    'Definition %s not implemented', definition.__name__)
                raise NotImplementedError(definition.__name__)

        # Generate functions:
        for ppci_function, signature, wasm_function in gen_functions:
            self.generate_function(ppci_function, signature, wasm_function)

        # Generate run_init function:
        self.gen_init_procedure(tables, global_inits, start_function_id)

        function_names = [f[0].name for f in self.functions]
        global_names = [g for g in self.globalz]

        # TODO: hack to pass this information alongside module
        self.builder.module._wasm_function_names = function_names
        self.builder.module._wasm_globals = global_names

        return self.builder.module

    def gen_init_procedure(self, tables, global_inits, start_function_ref):
        """ Generate an initialization procedure.

        - Initializes eventual function tables.
        - Calls an optionalstart procedure.
        """
        ppci_function = self.builder.new_procedure('_run_init')
        self.builder.set_function(ppci_function)
        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        # Initialize global values:
        # (This must be done here, since initial values may contain imported globals)
        for g2, init in global_inits:
            value = self.gen_expression(init)
            self.emit(ir.Store(value, g2))
            
        # Fill function pointer tables:
        # TODO: we might be able to do this at link time?
        for table_variable, elems in tables:
            # TODO: what if alignment is bigger than size?
            assert self.ptr_info.size == self.ptr_info.alignment
            ptr_size = self.emit(
                ir.Const(self.ptr_info.size, 'ptr_size', ir.ptr))

            # Loop over elems which initialize table:
            for offset, functions in elems:
                # Start at the bottom of the variable table:
                address = table_variable

                # Add offset:
                offset_value = self.gen_expression(offset)
                assert offset_value.ty is ir.i32
                offset_value = self.emit(ir.Cast(offset_value, 'offset', ir.ptr))
                address = self.emit(
                    ir.add(address, offset_value, 'table_address', ir.ptr))

                for func in functions:
                    # Lookup function
                    value = self.functions[func.index][0]
                    self.emit(ir.Store(value, address))
                    address = self.emit(
                        ir.add(address, ptr_size, 'table_address', ir.ptr))

        # Call eventual start function:
        if start_function_ref is not None:
            target, _ = self.functions[start_function_ref.index]
            self.emit(ir.ProcedureCall(target, []))

        self.emit(ir.Exit())

        # Enter correct debug info:
        dbg_arg_types = []
        dbg_return_type = self.get_debug_type('void')
        db_function_info = debuginfo.DebugFunction(
            ppci_function.name,
            common.SourceLocation('main.wasm', 1, 1, 1),
            dbg_return_type, dbg_arg_types)
        self.debug_db.enter(ppci_function, db_function_info)

    def emit(self, ppci_inst):
        """ Emits the given instruction to the builder.
        """
        self.builder.emit(ppci_inst)
        return ppci_inst

    def new_block(self):
        self.blocknr += 1
        block_name = self.builder.function.name + '_block' + str(self.blocknr)
        self.logger.debug('creating block %s', block_name)
        return self.builder.new_block(block_name)

    TYP_MAP = {
        'i32': ir.i32, 'i64': ir.i64,
        'f32': ir.f32, 'f64': ir.f64,
    }

    def get_ir_type(self, wasm_type):
        wasm_type = wasm_type.split('.')[0]
        return self.TYP_MAP[wasm_type]

    def get_debug_type(self, name):
        if self.debug_db.contains(name):
            return self.debug_db.get(name)
        else:
            dbg_type_map = {
                'f32': debuginfo.DebugBaseType('float', 4, 1),
                'f64': debuginfo.DebugBaseType('double', 8, 1),
                'i32': debuginfo.DebugBaseType('int', 4, 1),
                'i64': debuginfo.DebugBaseType('long', 8, 1),
                'void': debuginfo.DebugBaseType('void', 0, 1),
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
            'Generating wasm function %s %s',
            ppci_function.name, signature.to_string())
        self.stack = []
        self.block_stack = []

        # Create correct debug signature for function:

        if signature.result:
            if len(signature.result) != 1:
                raise ValueError(
                    'Cannot handle {} return values'.format(
                        len(signature.result)))
            dbg_return_type = self.get_debug_type(signature.result[0])
        else:
            dbg_return_type = self.get_debug_type('void')
        self.builder.set_function(ppci_function)

        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        dbg_arg_types = []
        self.locals = []  # todo: ak: why store on self?
        # First locals are the function arguments:
        for i, a_typ in enumerate(signature.params):
            ir_typ = self.get_ir_type(a_typ[1])
            ir_arg = ir.Parameter('param{}'.format(i), ir_typ)
            dbg_arg_types.append(debuginfo.DebugParameter(
                'arg{}'.format(i), self.get_debug_type(a_typ[1])))
            ppci_function.add_parameter(ir_arg)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc('alloc{}'.format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, 'local{}'.format(i)))
            self.locals.append((ir_typ, addr))
            # Store parameter into local variable:
            self.emit(ir.Store(ir_arg, addr))

        # Enter correct debug info:
        db_function_info = debuginfo.DebugFunction(
            ppci_function.name,
            common.SourceLocation('main.wasm', 1, 1, 1),
            dbg_return_type, dbg_arg_types)
        self.debug_db.enter(ppci_function, db_function_info)

        # Next are the rest of the locals:
        for i, local in enumerate(wasm_function.locals, len(self.locals)):
            local_id, local_typ = local
            local_id = i if local_id is None else local_id
            ir_typ = self.get_ir_type(local_typ)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc('alloc{}'.format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, 'local{}'.format(i)))

            # Initialize local variable to zero:
            zero_init = self.emit(ir.Const(0, 'local_init', ir_typ))
            self.emit(ir.Store(zero_init, addr))

            self.locals.append((ir_typ, addr))

        # Create an implicit top level block:
        if isinstance(ppci_function, ir.Procedure):
            final_phi = None
        else:
            final_phi = ir.Phi('function_result', ppci_function.return_ty)
            self.logger.debug('Created phi %s', final_phi)
        body_block = self.new_block()
        final_block = self.new_block()
        self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.block_stack.append(
            BlockLevel('block', final_block, body_block, final_phi, 0))

        # Generate code for each instruction:
        num = len(wasm_function.instructions)
        for nr, instruction in enumerate(wasm_function.instructions, start=1):
            if self.verbose:
                self.logger.debug(
                    '%s/%s %s [stack=%s]',
                    nr, num,
                    instruction.to_string(), len(self.stack))
            self.generate_instruction(instruction)

        # Close of function:
        if final_phi:
            # print(self.stack)
            self.fill_phi(final_phi)

        self.block_stack.pop()
        assert not self.block_stack

        if self.is_reachable:
            self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)
        if isinstance(ppci_function, ir.Procedure):
            self.emit(ir.Exit())
        else:
            self.emit(final_phi)
            self.emit(ir.Return(final_phi))

        # Sometimes this assert throws:
        # TODO: enable the below assert:
        # assert not self.stack

        ppci_function.delete_unreachable()

    OPMAP = dict(
        eqz='==', eq='==', ne='!=',
        ge='>=', ge_u='>=', ge_s='>=',
        le='<=', le_u='<=', le_s='<=',
        gt='>', gt_u='>', gt_s='>',
        lt='<', lt_u='<', lt_s='<')

    def get_phi(self, instruction):
        """ Get phi function for the given loop/block/if """
        result_type = instruction.args[0]
        if result_type == 'emptyblock':
            phi = None
        else:
            ir_typ = self.get_ir_type(result_type)
            phi = ir.Phi('block_result', ir_typ)
            self.logger.debug('Created phi %s', phi)
        return phi

    def fill_phi(self, phi):
        """ Fill phi with current stack value, if phi is needed """
        if phi and self.is_reachable:
            self.logger.debug('Filling phi %s', phi)
            value = self.pop_value(ir_typ=phi.ty)
            assert self.builder.block is not None
            phi.set_incoming(self.builder.block, value)
            self.push_value(value)

    def pop_condition(self):
        """ Get comparison, a and b of the value stack """
        if len(self.stack) > self.block_stack[-1].stack_start:
            value = self.stack.pop()
            if isinstance(value, ir.Value):
                assert value.ty is ir.i32
                a = value
                b = self.emit(ir.Const(0, 'zero', ir.i32))
                return '!=', a, b
            else:
                return value
        else:
            raise ValueError('Value stack underflow')

    def pop_value(self, ir_typ=None):
        """ Pop a value of the stack """
        if len(self.stack) > self.block_stack[-1].stack_start:
            value = self.stack.pop()
            if isinstance(value, ir.Value):
                if ir_typ:
                    assert value.ty is ir_typ
                return value
            else:
                # Emit some sort of weird ternary operation!
                op, a, b = value

                ja = self.builder.new_block()
                nein = self.builder.new_block()
                immer = self.builder.new_block()
                self.emit(ir.CJump(a, op, b, ja, nein))

                self.builder.set_block(ja)
                one = self.emit(ir.Const(1, 'one', ir.i32))
                self.emit(ir.Jump(immer))

                self.builder.set_block(nein)
                zero = self.emit(ir.Const(0, 'zero', ir.i32))
                self.emit(ir.Jump(immer))

                self.builder.set_block(immer)
                phi = ir.Phi('ternary', ir.i32)
                phi.set_incoming(ja, one)
                phi.set_incoming(nein, zero)
                self.emit(phi)
                if ir_typ:
                    assert phi.ty is ir_typ
                return phi
        else:
            raise ValueError('Value stack underflow')

    def push_value(self, value):
        """ Put a value on top of the stack """
        self.stack.append(value)

    def unwind(self, block):
        """ Unwind the value stack """
        while len(self.stack) > block.stack_start:
            self.stack.pop()

    def generate_instruction(self, instruction):
        """ Generate ir-code for a single wasm instruction """
        inst = instruction.opcode

        # IMPORTANT: handle block instructions first
        # Then check if we are in unreachable code, and do not generate
        # instructions in the unreachable space:
        if inst == 'block':
            self.gen_block(instruction)

        elif inst == 'loop':
            self.gen_loop(instruction)

        elif inst == 'if':
            self.gen_if(instruction)

        elif inst == 'else':
            self.gen_else()

        elif inst == 'end':
            self.gen_end()

        elif not self.is_reachable:
            # This is a guarding condition for the other instructions
            pass

        elif inst in BINOPS:
            self.gen_binop(instruction)

        elif inst in CMPOPS:
            self.gen_cmpop(instruction)

        elif inst in STORE_OPS:
            self.gen_store(instruction)

        elif inst in LOAD_OPS:
            self.gen_load(instruction)

        elif inst in {
                'i32.wrap/i64',
                'i64.extend_s/i32',
                'i64.extend_u/i32',
                'f64.convert_s/i32',
                'f64.convert_u/i32',
                'f64.convert_s/i64',
                'f64.convert_u/i64',
                'f32.convert_s/i32',
                'f32.convert_u/i32',
                'f32.convert_s/i64',
                'f32.convert_u/i64',
                }:
            from_ir_typ = self.get_ir_type(inst.split('/')[1])
            ir_typ = self.get_ir_type(inst.split('.')[0])
            value = self.pop_value(ir_typ=from_ir_typ)
            if '_u' in inst:
                # First cast to unsigned value:
                mp = {
                    '_u/i32': ir.u32,
                    '_u/i64': ir.u64,
                }
                unsigned_ir_typ = mp[inst[-6:]]
                value = self.emit(ir.Cast(value, 'unsigned', unsigned_ir_typ))
            value = self.emit(ir.Cast(value, 'cast', ir_typ))
            self.push_value(value)

        elif inst in {
                'i32.trunc_s/f32',
                'i32.trunc_u/f32',
                'i32.trunc_s/f64',
                'i32.trunc_u/f64',
                'i64.trunc_s/f32',
                'i64.trunc_u/f32',
                'i64.trunc_s/f64',
                'i64.trunc_u/f64',
                }:
            # TODO: in theory this should be solvable in ir-code.
            if True:
                self._runtime_call(inst)
            else:
                from_ir_typ = self.get_ir_type(inst.split('/')[1])
                ir_typ = self.get_ir_type(inst.split('.')[0])
                value = self.pop_value(ir_typ=from_ir_typ)
                if '_u' in inst:
                    # First cast to unsigned value:
                    mp = {
                        'i32.trunc_u': ir.u32,
                        'i64.trunc_u': ir.u64,
                    }
                    unsigned_ir_typ = mp[inst.split('/')[0]]
                    value = self.emit(ir.Cast(
                        value, 'unsigned', unsigned_ir_typ))
                value = self.emit(ir.Cast(value, 'cast', ir_typ))
                self.push_value(value)

        elif inst in {
                'f64.promote/f32',
                'f32.demote/f64',
                }:
            # TODO: in theory this should be solvable in ir-code.
            if True:
                self._runtime_call(inst)
            else:
                from_ir_typ = self.get_ir_type(inst.split('/')[1])
                ir_typ = self.get_ir_type(inst.split('.')[0])
                value = self.pop_value(ir_typ=from_ir_typ)
                value = self.emit(ir.Cast(value, 'cast', ir_typ))
                self.push_value(value)

        elif inst in [
                'f64.sqrt', 'f64.abs', 'f64.ceil', 'f64.trunc',
                'f64.nearest',
                'f64.min', 'f64.max', 'f64.copysign',
                'f32.sqrt', 'f32.abs', 'f32.ceil', 'f32.trunc',
                'f32.nearest',
                'f32.min', 'f32.max', 'f32.copysign',
                'f32.reinterpret/i32',
                'i64.clz', 'i64.ctz', 'i64.popcnt',
                'i64.rotl', 'i64.rotr',
                'f64.reinterpret/i64',
                'i64.reinterpret/f64',
                'i32.reinterpret/f32',
                'i32.clz', 'i32.ctz', 'i32.popcnt',
                'i32.rotl', 'i32.rotr',
                'memory.grow',
                'memory.size']:
            self._runtime_call(inst)

        elif inst in {'f64.const', 'f32.const', 'i64.const', 'i32.const'}:
            value = self.emit(
                ir.Const(
                    instruction.args[0], 'const', self.get_ir_type(inst)))
            self.push_value(value)

        elif inst in ['set_local', 'tee_local']:
            ty, local_var = self.locals[instruction.args[0].index]
            value = self.pop_value(ir_typ=ty)
            self.emit(ir.Store(value, local_var))
            if inst == 'tee_local':
                self.push_value(value)

        elif inst == 'get_local':
            ty, local_var = self.locals[instruction.args[0].index]
            value = self.emit(ir.Load(local_var, 'getlocal', ty))
            self.push_value(value)

        elif inst == 'get_global':
            ty, addr = self.globalz[instruction.args[0].index]
            value = self.emit(ir.Load(addr, 'get_global', ty))
            self.push_value(value)

        elif inst == 'set_global':
            ty, addr = self.globalz[instruction.args[0].index]
            value = self.pop_value(ir_typ=ty)
            self.emit(ir.Store(value, addr))

        elif inst in ['f64.floor', 'f32.floor']:
            self._runtime_call(inst)

            # TODO: this does not work for all cases:
            #ir_typ = self.get_ir_type(inst)
            #value = self.pop_value(ir_typ)
            #value = self.emit(ir.Cast(value, 'cast', ir.u64))
            #value = self.emit(ir.Cast(value, 'cast', ir_typ))
            #self.push_value(value)
            # Someday we may have a Unary op for this,
            # or a call into a native runtime lib?
            # value = self.emit(
            #     ir.Unop('floor', self.pop_value(ir_typ), 'floor', ir_typ))
            # self.push_value(value)

        elif inst in ['f64.neg', 'f32.neg']:
            ir_typ = self.get_ir_type(inst)
            value = self.emit(
                ir.Unop('-', self.pop_value(ir_typ), 'neg', ir_typ))
            self.push_value(value)

        elif inst == 'br':
            self.gen_br(instruction)

        elif inst == 'br_if':
            self.gen_br_if(instruction)

        elif inst == 'br_table':
            self.gen_br_table(instruction)

        elif inst == 'call':
            self.gen_call(instruction)

        elif inst == 'call_indirect':
            self.gen_call_indirect(instruction)

        elif inst == 'return':
            self.gen_return(instruction)

        elif inst == 'unreachable':
            self.gen_unreachable()

        elif inst == 'select':
            self.gen_select(instruction)

        elif inst == 'drop':
            # Drop value on the stack
            self.pop_value()

        elif inst == 'nop':
            pass  # Easy money :D

        else:  # pragma: no cover
            raise NotImplementedError(inst)

    def gen_binop(self, instruction):
        """ Generate code for binary operator """
        inst = instruction.opcode
        itype, opname = inst.split('.')
        op_map = {
            'add': '+', 'sub': '-', 'mul': '*',
            'div': '/',
            'div_s': '/', 'div_u': '/',
            'rem_s': '%', 'rem_u': '%',
            'and': '&', 'or': '|', 'xor': '^',
            'shl': '<<', 'shr_u': '>>', 'shr_s': '>>',
        }
        op = op_map[opname]
        name = 'op_{}'.format(opname)
        ir_typ = self.get_ir_type(itype)
        b = self.pop_value(ir_typ=ir_typ)
        a = self.pop_value(ir_typ=ir_typ)
        do_unsigned = '_u' in opname
        if do_unsigned:
            # Unsigned operation, first cast to unsigned:
            u_ir_typ = {
                ir.i32: ir.u32,
                ir.i64: ir.u64,
            }[ir_typ]
            a = self.emit(ir.Cast(a, 'cast', u_ir_typ))
            b = self.emit(ir.Cast(b, 'cast', u_ir_typ))
            value = self.emit(ir.Binop(a, op, b, name, u_ir_typ))
            value = self.emit(ir.Cast(value, 'cast', ir_typ))
        else:
            value = self.emit(ir.Binop(a, op, b, name, ir_typ))
        self.push_value(value)

    def gen_cmpop(self, instruction):
        """ Generate code for a comparison operation """
        inst = instruction.opcode
        itype, opname = inst.split('.')
        ir_typ = self.get_ir_type(itype)
        if opname in ['eqz']:
            b = self.emit(ir.Const(0, 'zero', ir_typ))
            a = self.pop_value(ir_typ=ir_typ)
        else:
            b = self.pop_value(ir_typ=ir_typ)
            a = self.pop_value(ir_typ=ir_typ)
        is_unsigned = '_u' in inst
        if is_unsigned:
            # Cast to unsigned
            u_ir_typ = {
                ir.i32: ir.u32,
                ir.i64: ir.u64,
            }[ir_typ]
            a = self.emit(ir.Cast(a, 'cast', u_ir_typ))
            b = self.emit(ir.Cast(b, 'cast', u_ir_typ))

        op = self.OPMAP[opname]
        self.push_value((op, a, b))
        # todo: hack; we assume this is the only test in an if

    def gen_load(self, instruction):
        """ Generate code for load instruction """
        itype, load_op = instruction.opcode.split('.')
        ir_typ = self.get_ir_type(itype)
        _, offset = instruction.args
        address = self.get_memory_address(offset)
        if load_op == 'load':
            value = self.emit(ir.Load(address, 'load', ir_typ))
        else:
            # Load different data-type and cast:
            load_ir_typ = {
                'load8_u': ir.u8, 'load8_s': ir.i8,
                'load16_u': ir.u16, 'load16_s': ir.i16,
                'load32_u': ir.u32, 'load32_s': ir.i32,
            }[load_op]
            value = self.emit(ir.Load(address, 'load', load_ir_typ))
            value = self.emit(ir.Cast(value, 'casted_load', ir_typ))
        self.push_value(value)

    def gen_store(self, instruction):
        """ Generate code for store instruction """
        itype, store_op = instruction.opcode.split('.')
        ir_typ = self.get_ir_type(itype)
        # ACHTUNG: alignment and offset are swapped in text:
        _, offset = instruction.args
        value = self.pop_value(ir_typ=ir_typ)
        address = self.get_memory_address(offset)
        if store_op == 'store':
            self.emit(ir.Store(value, address))
        else:
            store_ir_typ = {
                'store8': ir.i8, 'store16': ir.i16, 'store32': ir.i32,
            }[store_op]
            value = self.emit(
                ir.Cast(value, 'casted_value', store_ir_typ))
            self.emit(ir.Store(value, address))

    def get_memory_address(self, offset):
        """ Emit code to retrieve a memory address """
        base = self.pop_value()
        if base.ty is not ir.ptr:
            base = self.emit(ir.Cast(base, 'cast', ir.ptr))
        offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
        address = self.emit(ir.add(base, offset, 'address', ir.ptr))
        mem0 = self.emit(ir.Load(self.memory_base_address, 'mem0', ir.ptr))
        address = self.emit(ir.add(mem0, address, 'address', ir.ptr))
        return address

    @property
    def is_reachable(self):
        """ Determine if the current position is reachable """
        # Attention:
        # Since block implements iter, one cannot check for bool(block) if
        # the block is empty.. So we have to check for None here:
        return self.builder.block is not None

    def gen_block(self, instruction):
        """ Generate start of block """
        if self.is_reachable:
            self.logger.debug('start of block')
            phi = self.get_phi(instruction)
            inner_block = self.new_block()
            continue_block = self.new_block()
            self.emit(ir.Jump(inner_block))
            self.builder.set_block(inner_block)
        else:
            self.logger.debug('start of unreachable block')
            phi = None
            inner_block = None
            continue_block = None
        self.block_stack.append(
            BlockLevel(
                'block', continue_block, inner_block, phi, len(self.stack)))

    def gen_loop(self, instruction):
        """ Generate code for a loop start """
        if self.is_reachable:
            phi = self.get_phi(instruction)
            inner_block = self.new_block()
            continue_block = self.new_block()
            self.emit(ir.Jump(inner_block))
            self.builder.set_block(inner_block)
        else:
            phi = None
            inner_block = None
            continue_block = None
        self.block_stack.append(
            BlockLevel(
                'loop', continue_block, inner_block, phi, len(self.stack)))

    def gen_end(self):
        """ Generate code for end instruction.

        This is a more or less complex task. It has to deal with unreachable
        code as well.
        """
        block = self.block_stack[-1]
        if block.phi and self.is_reachable:
            self.fill_phi(block.phi)

        # The value stack may contain more items, clear them off
        self.block_stack.pop()
        self.unwind(block)

        # If we are not unreachable:
        if self.is_reachable:
            assert block.continue_block is not None
            self.emit(ir.Jump(block.continue_block))

        if block.typ == 'if' and block.inner_block is not None:
            # We should connect empty else to end block.
            self.builder.set_block(block.inner_block)
            self.emit(ir.Jump(block.continue_block))

        self.builder.set_block(block.continue_block)

        if block.phi:
            # if we close a block that yields a value introduce a phi
            self.logger.debug('Put %s on stack', block.phi)
            self.emit(block.phi)
            self.push_value(block.phi)

    def gen_if(self, instruction):
        """ Generate code for an if start """
        if self.is_reachable:
            # todo: we assume that the test is a comparison
            op, a, b = self.pop_condition()
            true_block = self.new_block()
            continue_block = self.new_block()
            else_block = self.new_block()
            self.emit(ir.CJump(a, op, b, true_block, else_block))
            self.builder.set_block(true_block)
            phi = self.get_phi(instruction)
        else:
            continue_block = None
            else_block = None
            phi = None
        # Store else block as inner block to allow break:
        self.block_stack.append(
            BlockLevel('if', continue_block, else_block, phi, len(self.stack)))

    def gen_else(self):
        """ Generate code for else instruction """
        if_block = self.block_stack[-1]
        assert if_block.typ == 'if'
        if if_block.phi:
            self.fill_phi(if_block.phi)

        self.block_stack.pop()
        self.unwind(if_block)

        # else_block was stored in inner block
        else_block = if_block.inner_block
        continue_block = if_block.continue_block

        if self.is_reachable:
            self.emit(ir.Jump(continue_block))
        self.builder.set_block(else_block)
        self.block_stack.append(
            BlockLevel(
                'else', continue_block, None, if_block.phi,
                if_block.stack_start))

    def gen_call(self, instruction):
        """ Generate a function call """
        # Call another function!
        idx = instruction.args[0].index
        ir_function, signature = self.functions[idx]
        self._gen_call_helper(ir_function, signature)

    def gen_call_indirect(self, instruction):
        """ Call another function by pointer! """
        type_id = instruction.args[0].index
        signature = self.wasm_types[type_id]
        func_index = self.pop_value()
        ptr_size = self.emit(ir.Const(self.ptr_info.size, 'ptr_size', ir.i32))
        element_offset = self.emit(ir.Cast(
            self.emit(ir.mul(func_index, ptr_size, 'element_offset', ir.i32)),
            'element_offset', ir.ptr))
        element_address = self.emit(ir.add(
            self.table_var, element_offset, 'element_address', ir.ptr))
        func_ptr = self.emit(ir.Load(element_address, 'func_ptr', ir.ptr))
        # TODO: how to check function type during runtime?

        self._gen_call_helper(func_ptr, signature)

    def _gen_call_helper(self, target, signature):
        """ Common function calling logic """
        self.logger.debug(
            'Calling function %s with signature %s',
            target, signature.to_string())

        args = [self.pop_value() for _ in range(len(signature.params))]
        # Note that the top of the stack contains the last argument:
        args.reverse()
        for arg, arg_type in zip(args, signature.params):
            ir_typ = self.get_ir_type(arg_type[1])
            assert arg.ty is ir_typ

        if signature.result:
            assert len(signature.result) == 1
            ir_typ = self.get_ir_type(signature.result[0])
            value = self.emit(
                ir.FunctionCall(target, args, 'call', ir_typ))
            self.push_value(value)
        else:
            self.emit(ir.ProcedureCall(target, args))

    def gen_select(self, instruction):
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
        phi = ir.Phi('ternary', ja_value.ty)
        phi.set_incoming(ja_block, ja_value)
        phi.set_incoming(nein_block, nein_value)
        self.emit(phi)
        self.push_value(phi)

    def gen_unreachable(self):
        """ Generate appropriate code for an unreachable instruction.

        What we will do, is we call an external function to handle this
        exception. Also we will return from the subroutine.
        """
        self._runtime_call('unreachable')
        if isinstance(self.builder.function, ir.Procedure):
            self.emit(ir.Exit())
        else:
            # TODO: massive hack just to return some value:
            # TODO: do we need ir.Unreachable()?
            v = self.emit(ir.Const(
                0, 'unreachable', self.builder.function.return_ty))
            self.emit(ir.Return(v))
        self.builder.set_block(None)

    def gen_return(self, instruction):
        """ Generate code for return instruction.

        Treat return as a break to the top level block.
        """
        targetblock = self.block_stack[0].continue_block
        self.fill_phi(self.block_stack[0].phi)
        self.emit(ir.Jump(targetblock))
        self.builder.set_block(None)

    def gen_br(self, instruction):
        """ Generate code for br instruction """
        depth = instruction.args[0]
        targetblock = self.do_jump(depth)
        self.emit(ir.Jump(targetblock))
        self.builder.set_block(None)

    def gen_br_if(self, instruction):
        """ Generate code for br_if instruction """
        op, a, b = self.pop_condition()
        depth = instruction.args[0]
        targetblock = self.do_jump(depth)
        falseblock = self.new_block()
        self.emit(ir.CJump(a, op, b, targetblock, falseblock))
        self.builder.set_block(falseblock)

    def do_jump(self, depth):
        """ Lookup the branch target and fill its optional value.

        Note: the name of this function is not ideal.
        """
        assert isinstance(depth, components.Ref)
        depth = depth.index
        block = self.block_stack[-depth-1]
        if block.typ == 'loop':
            # assert not block.phi
            targetblock = block.inner_block
        else:
            self.fill_phi(block.phi)
            targetblock = block.continue_block
        return targetblock

    def gen_br_table(self, instruction):
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
            target_block = self.do_jump(depth)
            ja_block = target_block
            nein_block = self.new_block()
            c = self.emit(ir.Const(i, 'label', ir_typ))
            self.emit(ir.CJump(test_value, '==', c, ja_block, nein_block))
            self.builder.set_block(nein_block)

        # Determine default block:
        depth = default_label
        target_block = self.do_jump(depth)
        default_block = target_block
        self.emit(ir.Jump(default_block))
        self.builder.set_block(None)

    def _runtime_call(self, inst):
        """ Generate runtime function call.

        This is required for functions such 'sqrt' as which do not have
        a reasonable ppci ir-code equivalent.
        """
        rt_func_name = 'wasm_rt_' + sanitize_name(inst)

        # Determine argument and return types:
        stack_in, stack_out = STACK_IO[inst]
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

        args = []
        for arg_ir_typ in reversed(arg_types):
            arg = self.pop_value(ir_typ=arg_ir_typ)
            assert arg.ty is arg_ir_typ
            args.append(arg)
        args.reverse()
        if ir_typ is None:
            value = self.emit(
                ir.ProcedureCall(rt_func, args))
        else:
            value = self.emit(
                ir.FunctionCall(rt_func, args, 'rtlib_call_result', ir_typ))
            self.push_value(value)


class BlockLevel:
    def __init__(self, typ, continue_block, inner_block, phi, stack_start):
        self.typ = typ
        self.continue_block = continue_block
        self.inner_block = inner_block
        self.phi = phi
        self.stack_start = stack_start
