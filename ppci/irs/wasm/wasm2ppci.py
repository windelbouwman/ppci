""" Convert Web Assembly (WASM) into PPCI IR. """

import logging
import struct
from ... import ir
from ... import irutils
from ... import common
from ...binutils import debuginfo
from . import components
from ._opcodes import STORE_OPS, LOAD_OPS


def wasm_to_ir(wasm_module: components.Module) -> ir.Module:
    """ Convert a WASM module into a PPCI native module.

    Args:
        wasm_module (ppci.irs.wasm.Module): The wasm-module to compile

    Returns:
        An IR-module.
    """
    compiler = WasmToIrCompiler()
    ppci_module = compiler.generate(wasm_module)
    return ppci_module


class WasmToIrCompiler:
    """ Convert WASM instructions into PPCI IR instructions.
    """
    logger = logging.getLogger('wasm2ir')
    verbose = True

    def __init__(self):
        self.builder = irutils.Builder()
        self.blocknr = 0

    def generate(self, wasm_module: components.Module):
        assert isinstance(wasm_module, components.Module)

        # First read all sections:
        # for wasm_function in wasm_module.sections[-1].functiondefs:
        self.wasm_types = []
        self.globalz = []
        function_sigs = []
        function_defs = []
        functions = []
        self.function_space = []
        self.function_names = {}
        for section in wasm_module:
            if isinstance(section, components.TypeSection):
                self.wasm_types.extend(section.functionsigs)
            elif isinstance(section, components.ImportSection):
                for im in section.imports:
                    name = im.fieldname
                    if im.kind == 'func':
                        sig = self.wasm_types[im.type_id]
                        self.function_names[len(self.function_space)] = name
                        self.function_space.append(sig)
                    else:
                        raise NotImplementedError(im.kind)
            elif isinstance(section, components.ExportSection):
                for x in section.exports:
                    if x.kind == 'func':
                        # print(x.index)
                        # f = self.function_space[x.index]
                        # f = x.name, f[1]
                        self.function_names[x.index] = x.name
                    else:
                        pass
                        # raise NotImplementedError(x.kind)
            elif isinstance(section, components.CodeSection):
                function_defs.extend(section.functiondefs)
                assert len(function_sigs) == len(function_defs)
                for sig_index, wasm_function in zip(
                        function_sigs, function_defs):
                    signature = self.wasm_types[sig_index]
                    index = len(self.function_space)
                    self.function_space.append(signature)
                    if index in self.function_names:
                        name = self.function_names[index]
                    else:
                        name = 'unnamed{}'.format(index)
                        self.function_names[index] = name
                    functions.append((name, signature, wasm_function))
            elif isinstance(section, components.GlobalSection):
                for i, g in enumerate(section.globalz):
                    ir_typ = self.get_ir_type(g.typ)
                    fmts = {
                        ir.i32: '<i', ir.i64: '<q',
                        ir.f32: 'f', ir.f64: 'd',
                    }
                    fmt = fmts[ir_typ]
                    size = struct.calcsize(fmt)
                    value = struct.pack(fmt, g.value)
                    g2 = ir.Variable(
                        'global{}'.format(i), size, size, value=value)
                    self.globalz.append((ir_typ, g2))
            elif isinstance(section, components.DataSection):
                pass
            elif isinstance(section, components.FunctionSection):
                function_sigs.extend(section.indices)
            else:
                self.logger.error('Section %s not handled', section)

        # Create module:
        self.debug_db = debuginfo.DebugDb()
        self.builder.module = ir.Module('mainmodule', debug_db=self.debug_db)

        # Generate functions:
        for name, signature, wasm_function in functions:
            self.generate_function(name, signature, wasm_function)

        return self.builder.module

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

    def generate_function(self, name, signature, wasm_function):
        """ Generate code for a single function """
        self.logger.debug(
            'Generating wasm function %s %s', name, signature.to_text())
        self.stack = []
        self.block_stack = []

        if signature.returns:
            if len(signature.returns) != 1:
                raise ValueError(
                    'Cannot handle {} return values'.format(
                        len(signature.returns)))
            ret_type = self.get_ir_type(signature.returns[0])
            ppci_function = self.builder.new_function(name, ret_type)
        else:
            ppci_function = self.builder.new_procedure(name)
        self.builder.set_function(ppci_function)

        db_float = debuginfo.DebugBaseType('double', 8, 1)
        db_function_info = debuginfo.DebugFunction(
            name,
            common.SourceLocation('main.wasm', 1, 1, 1),
            db_float, ())
        self.debug_db.enter(ppci_function, db_function_info)

        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        self.locals = []
        # First locals are the function arguments:
        for i, a_typ in enumerate(signature.params):
            ir_typ = self.get_ir_type(a_typ)
            ir_arg = ir.Parameter('param{}'.format(i), ir_typ)
            ppci_function.add_parameter(ir_arg)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc('alloc{}'.format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, 'local{}'.format(i)))
            self.locals.append((ir_typ, addr))
            # Store parameter into local variable:
            self.emit(ir.Store(ir_arg, addr))

        # Next are the rest of the locals:
        for i, local in enumerate(wasm_function.locals, len(self.locals)):
            ir_typ = self.get_ir_type(local)
            size = ir_typ.size
            alignment = size
            alloc = self.emit(ir.Alloc('alloc{}'.format(i), size, alignment))
            addr = self.emit(ir.AddressOf(alloc, 'local{}'.format(i)))
            self.locals.append((ir_typ, addr))

        num = len(wasm_function.instructions)
        for nr, instruction in enumerate(wasm_function.instructions, start=1):
            if self.verbose:
                self.logger.debug('%s/%s %s', nr, num, instruction.to_text())
            self.generate_instruction(instruction)

        # Add terminating instruction if block is non empty:
        if (not self.builder.block.is_empty) and \
                (not self.builder.block.is_closed):
            if isinstance(ppci_function, ir.Procedure):
                self.emit(ir.Exit())
            else:
                return_value = self.pop_value()
                self.emit(ir.Return(return_value))

        # ppci_function.dump()
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
        'f64.reinterpret/i64',  # TODO: this is not a cast?
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
                'rotr': 'ror', 'rotl': 'rol'}
            op = op_map[opname]
            b, a = self.pop_value(), self.pop_value()
            value = self.emit(
                ir.Binop(a, op, b, opname, self.get_ir_type(itype)))
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
            itype = inst.split('.')[0]
            ir_typ = self.get_ir_type(itype)
            offset, align = instruction.args
            value = self.pop_value()
            base = self.pop_value()
            if base.ty is not ir.ptr:
                base = self.emit(ir.Cast(base, 'cast', ir.ptr))
            offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
            address = self.emit(ir.add(base, offset, 'address', ir.ptr))
            self.emit(ir.Store(value, address))

        elif inst in LOAD_OPS:
            itype = inst.split('.')[0]
            ir_typ = self.get_ir_type(itype)
            offset, align = instruction.args
            base = self.pop_value()
            if base.ty is not ir.ptr:
                base = self.emit(ir.Cast(base, 'cast', ir.ptr))
            offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
            address = self.emit(ir.add(base, offset, 'address', ir.ptr))
            value = self.emit(ir.Load(address, 'load', ir_typ))
            self.stack.append(value)

        elif inst in self.CASTOPS:
            value = self.pop_value()
            ir_typ = self.get_ir_type(inst.split('.')[0])
            value = self.emit(ir.Cast(value, 'cast', ir_typ))
            self.stack.append(value)

        elif inst == 'f64.floor':
            value1 = self.emit(
                ir.Cast(self.pop_value(), 'floor_cast_1', ir.i64))
            value2 = self.emit(ir.Cast(value1, 'floor_cast_2', ir.f64))
            self.stack.append(value2)

        elif inst == 'f64.sqrt':
            # TODO: implement library call?
            pass
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

        elif inst == 'f64.neg':
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
            # TODO: what to do? Call a runtime function?
            pass
        elif inst == 'select':
            self.gen_select(instruction)
        elif inst == 'drop':
            # Drop value on the stack
            self.pop_value()
        else:  # pragma: no cover
            raise NotImplementedError(inst)

    def gen_call(self, instruction):
        """ Generate a function call """
        # Call another function!
        idx = instruction.args[0]
        sig = self.function_space[idx]
        name = self.function_names[idx]

        args = []
        for arg_type in sig.params:
            args.append(self.pop_value())

        if sig.returns:
            assert len(sig.returns) == 1
            ir_typ = self.get_ir_type(sig.returns[0])
            value = self.emit(ir.FunctionCall(name, args, 'call', ir_typ))
            self.stack.append(value)
        else:
            self.emit(ir.ProcedureCall(name, args))

    def gen_call_indirect(self, instruction):
        # Call another function by pointer!
        type_id = instruction.args[0]
        signature = self.wasm_types[type_id]
        func_ptr = self.pop_value()
        if func_ptr.ty is not ir.ptr:
            func_ptr = self.emit(ir.Cast(func_ptr, 'ptr', ir.ptr))

        args = []
        for arg_type in signature.params:
            args.append(self.pop_value())

        if signature.returns:
            assert len(signature.returns) == 1
            ir_typ = self.get_ir_type(signature.returns[0])
            value = self.emit(
                ir.FunctionPointerCall(func_ptr, args, 'call', ir_typ))
            self.stack.append(value)
        else:
            self.emit(ir.ProcedurePointerCall(func_ptr, args))

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
