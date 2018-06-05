""" Convert Web Assembly (WASM) into PPCI IR. """

import logging
import struct
from .. import ir
from .. import irutils
from .. import common
from ..binutils import debuginfo
from ..arch.arch_info import TypeInfo
from . import components
from .opcodes import STORE_OPS, LOAD_OPS


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
    memories = {}
    memory_ids = []
    initializations = []
    for definition in wasm_module:
        if isinstance(definition, components.Memory):
            minsize = definition.min
            memories[definition.id] = bytearray(minsize * 65536)
            memory_ids.append(definition.id)
        elif isinstance(definition, components.Data):
            assert definition.offset.opcode == 'i32.const'
            offset = definition.offset.args[0]
            memory_id = definition.ref
            # TODO: should ref always be an integer index?
            if isinstance(memory_id, int):
                memory_id = memory_ids[memory_id]
            data = definition.data
            initializations.append((memory_id, offset, data))

    # Initialize various parts:
    for memory_id, offset, data in initializations:
        memory = memories[memory_id]
        memory[offset:offset+len(data)] = data

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
        self.wasm_types = {}  # id -> wasm.Type (signature)
        self.globalz = {}  # id -> (type, ir.Variable)
        functions = []
        self.function_names = {}  # Try to have a nice name
        self._runtime_functions = {}  # Function required during runtime
        export_names = {}  # mapping of id's to exported function names
        start_function_id = None
        tables = []  # Function pointer tables

        # Create a global pointer to the memory base address:
        self.memory_base_address = ir.Variable(
            'wasm_mem0_address', self.ptr_info.size, self.ptr_info.alignment)
        self.builder.module.add_variable(self.memory_base_address)

        for definition in wasm_module:
            if isinstance(definition, components.Type):
                self.wasm_types[definition.id] = definition

            elif isinstance(definition, components.Import):
                # name = definition.name
                if definition.kind == 'func':
                    index = definition.id
                    sig = self.wasm_types[definition.info[0]]
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
                    if index in self.function_names:
                        raise ValueError(
                            'Index {} already imported'.format(index))
                    assert index not in self.function_names
                    self.function_names[index] = extern_ir_function, sig
                else:
                    raise NotImplementedError(definition.kind)

            elif isinstance(definition, components.Export):
                if definition.kind == 'func':
                    # print(x.index)
                    # f = self.function_space[x.index]
                    # f = x.name, f[1]
                    assert definition.ref not in export_names
                    export_names[definition.ref] = definition.name
                else:
                    pass
                    # raise NotImplementedError(x.kind)

            elif isinstance(definition, components.Start):
                # Generate a procedure which calls the start procedure:
                start_function_id = definition.ref

            elif isinstance(definition, components.Func):
                signature = self.wasm_types[definition.ref]
                # Set name of function. If we have a string id prefer that,
                # otherwise we may have a name from import/export,
                # otherwise use index
                if isinstance(definition.id, str):
                    name = definition.id.lstrip('$')
                elif definition.id in export_names:
                    name = export_names[definition.id]
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

                assert definition.id not in self.function_names
                self.function_names[definition.id] = ppci_function, signature
                functions.append((ppci_function, signature, definition))

            elif isinstance(definition, components.Table):
                assert definition.id in (0, '$0')
                if definition.kind != 'anyfunc':
                    raise NotImplementedError('Non function pointer tables')
                assert definition.min == definition.max
                size = definition.max * self.ptr_info.size
                self.table_var = ir.Variable(
                    'func_table', size, self.ptr_info.alignment)
                self.builder.module.add_variable(self.table_var)
                tables.append((self.table_var, []))

            elif isinstance(definition, components.Elem):
                offset = definition.offset.args[0]
                assert offset == 0
                for ref in definition.refs:
                    tables[0][1].append(ref)

            elif isinstance(definition, components.Global):
                ir_typ = self.get_ir_type(definition.typ)
                fmts = {
                    ir.i32: '<i', ir.i64: '<q',
                    ir.f32: 'f', ir.f64: 'd',
                }
                fmt = fmts[ir_typ]
                size = struct.calcsize(fmt)
                # assume init is (f64.const xx):
                value = struct.pack(fmt, definition.init.args[0])
                g2 = ir.Variable(
                    'global{}'.format(definition.id), size, size, value=value)
                self.globalz[definition.id] = (ir_typ, g2)
            elif isinstance(definition, (components.Memory, components.Data)):
                # Data and memory are intended for the runtime to handle.
                pass

            else:
                # todo: Table, Element, Memory, Data
                self.logger.error(
                    'Definition %s not implemented', definition.__name__)
                raise NotImplementedError(definition.__name__)

        # Generate functions:
        for ppci_function, signature, wasm_function in functions:
            self.generate_function(ppci_function, signature, wasm_function)

        # Generate run_init function:
        self.gen_init_procedure(tables, start_function_id)

        return self.builder.module

    def gen_init_procedure(self, tables, start_function_id):
        """ Generate an initialization procedure.

        - Initializes eventual function tables.
        - Calls an optionalstart procedure.
        """
        ppci_function = self.builder.new_procedure('_run_init')
        self.builder.set_function(ppci_function)
        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        # Fill function pointer tables:
        # TODO: we might be able to do this at link time?
        for table_variable, functions in tables:
            # TODO: what if alignment is bigger than size?
            assert self.ptr_info.size == self.ptr_info.alignment
            ptr_size = self.emit(
                ir.Const(self.ptr_info.size, 'ptr_size', ir.ptr))

            # Start at the bottom of the variable table:
            address = table_variable
            for func in functions:
                # Lookup function
                value = self.function_names[func][0]
                self.emit(ir.Store(value, address))
                address = self.emit(
                    ir.add(address, ptr_size, 'table_address', ir.ptr))

        # Call eventual start function:
        if start_function_id is not None:
            target, _ = self.function_names[start_function_id]
            self.emit(ir.ProcedureCall(target, []))

        self.emit(ir.Exit())

        # Enter correct debug info:
        dbg_arg_types = []
        dbg_return_type = debuginfo.DebugBaseType('void', 0, 1)
        db_function_info = debuginfo.DebugFunction(
            ppci_function.name,
            common.SourceLocation('main.wasm', 1, 1, 1),
            dbg_return_type, dbg_arg_types)
        self.debug_db.enter(ppci_function, db_function_info)

    def emit(self, ppci_inst):
        """ Emits the given instruction to the builder.

        Can be muted for constants.
        """
        self.builder.emit(ppci_inst)
        return ppci_inst

    def new_block(self):
        self.blocknr += 1
        self.logger.debug('creating block %s', self.blocknr)
        block_name = self.builder.function.name + '_block' + str(self.blocknr)
        return self.builder.new_block(block_name)

    TYP_MAP = {
        'i32': ir.i32, 'i64': ir.i64,
        'f32': ir.f32, 'f64': ir.f64,
    }

    def get_ir_type(self, wasm_type):
        wasm_type = wasm_type.split('.')[0]
        return self.TYP_MAP[wasm_type]

    def generate_function(self, ppci_function, signature, wasm_function):
        """ Generate code for a single function """
        self.logger.info(
            'Generating wasm function %s %s',
            ppci_function.name, signature.to_string())
        self.stack = []
        self.block_stack = []

        # Create correct debug signature for function:
        dbg_type_map = {
            'f32': debuginfo.DebugBaseType('float', 4, 1),
            'f64': debuginfo.DebugBaseType('double', 8, 1),
            'i32': debuginfo.DebugBaseType('int', 4, 1),
            'i64': debuginfo.DebugBaseType('long', 8, 1),
        }

        if signature.result:
            if len(signature.result) != 1:
                raise ValueError(
                    'Cannot handle {} return values'.format(
                        len(signature.result)))
            dbg_return_type = dbg_type_map[signature.result[0]]
        else:
            dbg_return_type = debuginfo.DebugBaseType('void', 0, 1)
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
                'arg{}'.format(i), dbg_type_map[a_typ[1]]))
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
            self.locals.append((ir_typ, addr))

        num = len(wasm_function.instructions)
        for nr, instruction in enumerate(wasm_function.instructions, start=1):
            if self.verbose:
                self.logger.debug(
                    '%s/%s %s [stack=%s]',
                    nr, num,
                    instruction.to_string(), len(self.stack))
            self.generate_instruction(instruction)

        # Add terminating instruction if needed:
        if not self.builder.block.is_closed:
            if isinstance(ppci_function, ir.Procedure):
                self.emit(ir.Exit())
            else:
                if not self.builder.block.is_empty:
                    # if self.stack:
                    return_value = self.pop_value()
                    self.emit(ir.Return(return_value))
                # else:
                #    raise ValueError('No return value left on stack to pop')

        # Sometimes this assert throws:
        # TODO: enable the below assert:
        # assert not self.stack

        ppci_function.delete_unreachable()

    BINOPS = {
        'f64.add', 'f64.sub', 'f64.mul', 'f64.div',
        'f32.add', 'f32.sub', 'f32.mul', 'f32.div',
        'i64.add', 'i64.sub', 'i64.mul', 'i64.div_s', 'i64.div_u',
        'i32.add', 'i32.sub', 'i32.mul', 'i32.div_s', 'i32.div_u',
        'i64.and', 'i64.or', 'i64.xor',
        'i64.shl', 'i64.shr_s', 'i64.shr_u',
        'i64.rotl', 'i64.rotr',
        'i32.and', 'i32.or', 'i32.xor', 'i32.shl',
        'i32.shr_s', 'i32.shr_u',
        'i32.rotl', 'i32.rotr',
    }

    CASTOPS = {
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
    }

    CMPOPS = {
        'f64.eq', 'f64.ne', 'f64.ge', 'f64.gt', 'f64.le', 'f64.lt',
        'f32.eq', 'f32.ne', 'f32.ge', 'f32.gt', 'f32.le', 'f32.lt',
        'i32.eqz', 'i32.eq', 'i32.ne', 'i32.lt_s', 'i32.lt_u',
        'i32.gt_s', 'i32.gt_u', 'i32.le_s', 'i32.le_u',
        'i32.ge_s', 'i32.ge_u',
        'i64.eqz', 'i64.eq', 'i64.ne',
        'i64.lt_s', 'i64.lt_u',
        'i64.gt_s', 'i64.gt_u',
        'i64.le_s', 'i64.le_u',
        'i64.ge_s', 'i64.ge_u',
    }

    OPMAP = dict(
        eqz='==', eq='==', ne='!=',
        ge='>=', ge_u='>=', ge_s='>=',
        le='<=', le_u='<=', le_s='<=',
        gt='>', gt_u='>', gt_s='<',
        lt='<', lt_u='<', lt_s='<')

    def get_phi(self, instruction):
        """ Get phi function for the given loop/block/if """
        result_type = instruction.args[0]
        if result_type == 'emptyblock':
            phi = None
        else:
            ir_typ = self.get_ir_type(result_type)
            phi = ir.Phi('block_result', ir_typ)
        return phi

    def fill_phi(self, phi):
        """ Fill phi with current stack value, if phi is needed """
        if phi:
            # TODO: do we require stack 1 high?
            assert len(self.stack) == 1, str(self.stack)
            value = self.stack[-1]
            phi.set_incoming(self.builder.block, value)

    def pop_condition(self):
        """ Get comparison, a and b of the value stack """
        value = self.stack.pop()
        if isinstance(value, ir.Value):
            a = value
            b = self.emit(ir.Const(0, 'zero', ir.i32))
            return '!=', a, b
        else:
            return value

    def pop_value(self):
        """ Pop a value of the stack """
        value = self.stack.pop()
        if isinstance(value, ir.Value):
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
            return phi

    def generate_instruction(self, instruction):
        """ Generate ir-code for a single wasm instruction """
        inst = instruction.opcode
        if inst in self.BINOPS:
            itype, opname = inst.split('.')
            op_map = {
                'add': '+', 'sub': '-', 'mul': '*',
                'div': '/', 'div_s': '/', 'div_u': '/',
                'and': '&', 'or': '|', 'xor': '^', 'shl': '<<',
                'shr_u': '>>',
                # TODO: arithmatic shift right is not the same as
                # logical shift right.. TBD.
                'shr_s': 'asr',
                'rotr': 'ror', 'rotl': 'rol'}
            op = op_map[opname]
            name = 'op_{}'.format(opname)
            ir_typ = self.get_ir_type(itype)
            if op in ['ror', 'rol', 'asr']:
                self._runtime_call(inst, [ir_typ, ir_typ], ir_typ)
            else:
                b, a = self.pop_value(), self.pop_value()
                value = self.emit(ir.Binop(a, op, b, name, ir_typ))
                self.stack.append(value)

        elif inst in self.CMPOPS:
            itype, opname = inst.split('.')
            if opname in ['eqz']:
                b = self.emit(ir.Const(0, 'zero', self.get_ir_type(itype)))
                a = self.pop_value()
            else:
                b, a = self.stack.pop(), self.stack.pop()
            op = self.OPMAP[opname]
            self.stack.append((op, a, b))
            # todo: hack; we assume this is the only test in an if

        elif inst in STORE_OPS:
            # self.gen_store(inst)
            itype, store_op = inst.split('.')
            ir_typ = self.get_ir_type(itype)
            # ACHTUNG: alignment and offset are swapped in text:
            _, offset = instruction.args
            value = self.pop_value()
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

        elif inst in LOAD_OPS:
            itype, load_op = inst.split('.')
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
            self.stack.append(value)

        elif inst in self.CASTOPS:
            value = self.pop_value()
            ir_typ = self.get_ir_type(inst.split('.')[0])
            value = self.emit(ir.Cast(value, 'cast', ir_typ))
            self.stack.append(value)

        elif inst in ['f64.floor', 'f64.sqrt']:
            self._runtime_call(inst, [ir.f64], ir.f64)

        elif inst == 'i32.rem_u':
            self._runtime_call(inst, [ir.i32, ir.i32], ir.i32)

        elif inst == 'f64.reinterpret/i64':
            self._runtime_call(inst, [ir.i64], ir.f64)

        elif inst in ['i32.clz', 'i32.ctz', 'memory.grow']:
            self._runtime_call(inst, [ir.i32], ir.i32)

        elif inst in ['memory.size']:
            self._runtime_call(inst, [], ir.i32)

        elif inst in {'f64.const', 'f32.const', 'i64.const', 'i32.const'}:
            value = self.emit(
                ir.Const(
                    instruction.args[0], 'const', self.get_ir_type(inst)))
            self.stack.append(value)

        elif inst in ['set_local', 'tee_local']:
            value = self.pop_value()
            ty, local_var = self.locals[instruction.args[0]]
            assert ty is value.ty
            self.emit(ir.Store(value, local_var))
            if inst == 'tee_local':
                self.stack.append(value)

        elif inst == 'get_local':
            ty, local_var = self.locals[instruction.args[0]]
            value = self.emit(ir.Load(local_var, 'getlocal', ty))
            self.stack.append(value)

        elif inst == 'get_global':
            ty, addr = self.globalz[instruction.args[0]]
            value = self.emit(ir.Load(addr, 'get_global', ty))
            self.stack.append(value)

        elif inst == 'set_global':
            value = self.pop_value()
            ty, addr = self.globalz[instruction.args[0]]
            assert ty is value.ty
            self.emit(ir.Store(value, addr))

        elif inst in ['f64.neg', 'f32.neg']:
            value = self.emit(
                ir.Unop('-', self.pop_value(), 'neg', self.get_ir_type(inst)))
            self.stack.append(value)

        elif inst == 'block':
            phi = self.get_phi(instruction)
            innerblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.Jump(innerblock))
            self.builder.set_block(innerblock)
            self.block_stack.append(('block', continueblock, innerblock, phi))

        elif inst == 'loop':
            phi = self.get_phi(instruction)
            innerblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.Jump(innerblock))
            self.builder.set_block(innerblock)
            self.block_stack.append(('loop', continueblock, innerblock, phi))

        elif inst == 'br':
            depth = instruction.args[0]
            # TODO: can we break out of if-blocks?
            blocktype, continueblock, innerblock, phi = \
                self.block_stack[-depth-1]
            if blocktype == 'loop':
                targetblock = innerblock
            else:
                targetblock = continueblock
                self.fill_phi(phi)
            self.emit(ir.Jump(targetblock))
            falseblock = self.new_block()  # unreachable
            self.builder.set_block(falseblock)

        elif inst == 'br_if':
            self.gen_br_if(instruction)

        elif inst == 'br_table':
            self.gen_br_table(instruction)

        elif inst == 'if':
            # todo: we assume that the test is a comparison
            op, a, b = self.pop_condition()
            trueblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.CJump(a, op, b, trueblock, continueblock))
            self.builder.set_block(trueblock)
            phi = self.get_phi(instruction)
            self.block_stack.append(('if', continueblock, None, phi))

        elif inst == 'else':
            blocktype, continueblock, innerblock, phi = self.block_stack.pop()
            assert blocktype == 'if'
            elseblock = continueblock  # continueblock becomes elseblock
            continueblock = self.new_block()
            self.fill_phi(phi)
            if phi is not None:
                self.stack.pop()
            self.emit(ir.Jump(continueblock))
            self.builder.set_block(elseblock)
            self.block_stack.append(('else', continueblock, innerblock, phi))

        elif inst == 'end':
            blocktype, continueblock, innerblock, phi = self.block_stack.pop()
            self.fill_phi(phi)
            self.emit(ir.Jump(continueblock))
            self.builder.set_block(continueblock)
            # assert len(self.stack) == 0
            if phi is not None:
                # if we close a block that yields a value introduce a phi
                self.emit(phi)
                self.stack.append(phi)

        elif inst == 'call':
            self.gen_call(instruction)

        elif inst == 'call_indirect':
            self.gen_call_indirect(instruction)

        elif inst == 'return':
            if isinstance(self.builder.function, ir.Procedure):
                self.emit(ir.Exit())
            else:
                self.emit(ir.Return(self.pop_value()))
            after_return_block = self.new_block()
            self.builder.set_block(after_return_block)
            # TODO: assert that this was the last instruction

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

    def gen_call(self, instruction):
        """ Generate a function call """
        # Call another function!
        idx = instruction.args[0]
        ir_function, signature = self.function_names[idx]
        self._gen_call_helper(ir_function, signature)

    def gen_call_indirect(self, instruction):
        """ Call another function by pointer! """
        type_id = instruction.args[0]
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
            self.stack.append(value)
        else:
            self.emit(ir.ProcedureCall(target, args))

    def gen_select(self, instruction):
        """ Generate code for the select wasm instruction """
        # This is roughly equivalent to C-style: a ? b : c
        op, a, b = self.pop_condition()
        ja_value, nein_value = self.pop_value(), self.pop_value()

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
        self.stack.append(phi)

    def gen_unreachable(self):
        """ Generate appropriate code for an unreachable instruction.

        What we will do, is we call an external function to handle this
        exception. Also we will return from the subroutine.
        """
        self._runtime_call('unreachable', [], None)
        if isinstance(self.builder.function, ir.Procedure):
            self.emit(ir.Exit())
        else:
            # TODO: massive hack just to return some value:
            # TODO: do we need ir.Unreachable()?
            v = self.emit(ir.Const(
                0, 'unreachable', self.builder.function.return_ty))
            self.emit(ir.Return(v))
        after_return_block = self.new_block()
        self.builder.set_block(after_return_block)

    def gen_br_if(self, instruction):
        """ Generate code for br_if instruction """
        op, a, b = self.pop_condition()
        depth = instruction.args[0]
        blocktype, continueblock, innerblock, phi = \
            self.block_stack[-depth-1]
        if blocktype == 'loop':
            targetblock = innerblock
        else:
            targetblock = continueblock
        falseblock = self.new_block()
        self.emit(ir.CJump(a, op, b, targetblock, falseblock))
        self.builder.set_block(falseblock)

    def gen_br_table(self, instruction):
        """ Generate code for br_table instruction.
        This is a sort of switch case.

        This is called a jump table. Implement for now by chain of
        if else.
        """
        test_value = self.pop_value()
        assert test_value.ty in [ir.i32, ir.i64]
        ir_typ = test_value.ty
        option_labels = instruction.args[0]
        default_label = option_labels.pop(-1)
        for i, option_label in enumerate(option_labels):
            # Figure which block we must jump to:
            depth = option_label
            blocktype, continueblock, innerblock, phi = \
                self.block_stack[-depth-1]
            assert not phi
            if blocktype == 'loop':
                target_block = innerblock
            else:
                target_block = continueblock
            ja_block = target_block
            nein_block = self.new_block()
            c = self.emit(ir.Const(i, 'label', ir_typ))
            self.emit(ir.CJump(test_value, '==', c, ja_block, nein_block))
            self.builder.set_block(nein_block)

        # Determine default block:
        depth = default_label
        blocktype, continueblock, innerblock, phi = self.block_stack[-depth-1]
        assert not phi
        if blocktype == 'loop':
            target_block = innerblock
        else:
            target_block = continueblock
        default_block = target_block
        new_block = self.new_block()
        self.emit(ir.Jump(default_block))
        self.builder.set_block(new_block)
        # raise NotImplementedError(inst)

    def _runtime_call(self, rt_func_name, arg_types, ir_typ):
        """ Generate runtime function call.

        This is required for functions such 'sqrt' as which do not have
        a reasonable ppci ir-code equivalent.
        """
        rt_func_name = rt_func_name.replace('.', '_')

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
        for arg_typ in reversed(arg_types):
            arg = self.pop_value()
            assert arg.ty is arg_typ
            args.append(arg)
        args.reverse()
        if ir_typ is None:
            value = self.emit(
                ir.ProcedureCall(rt_func, args))
        else:
            value = self.emit(
                ir.FunctionCall(rt_func, args, 'rtlib_call_result', ir_typ))
            self.stack.append(value)
