""" Convert Web Assembly (WASM) into PPCI IR. """

import logging
from ... import ir
from ... import irutils
from ... import common
from ...binutils import debuginfo

from . import Module


def wasm_to_ppci(wasm_module, debug_db=None):
    """ Convert a WASM module into a PPCI native module. """
    compiler = Wasm2PpciCompiler()
    ppci_module = compiler.generate(wasm_module, debug_db)
    return ppci_module


class Wasm2PpciCompiler:
    """ Convert WASM instructions into PPCI IR instructions.
    """
    logger = logging.getLogger('wasm2ir')

    def __init__(self):
        self.builder = irutils.Builder()
        self.blocknr = 0

    def generate(self, wasm_module, debug_db=None):
        assert isinstance(wasm_module, Module)

        self.builder.module = ir.Module('mainmodule')

        for wasm_function in wasm_module.sections[-1].functiondefs:
            self.generate_function(wasm_function, debug_db)

        return self.builder.module

    def emit(self, ppci_inst):
        """
            Emits the given instruction to the builder.
            Can be muted for constants.
        """
        self.builder.emit(ppci_inst)
        return ppci_inst

    def new_block(self):
        self.blocknr += 1
        self.logger.debug('creating block %s', self.blocknr)
        return self.builder.new_block('block' + str(self.blocknr))

    def get_ir_type(self, wasm_type):
        wasm_type = wasm_type.split('.')[0]
        return ir.f64  # todo: temporary hack; map 1-to-1

    def generate_function(self, wasm_function, debug_db):
        self.stack = []
        self.block_stack = []

        ppci_function = self.builder.new_function('main', self.get_ir_type(''))
        self.builder.set_function(ppci_function)

        db_float = debuginfo.DebugBaseType('double', 8, 1)
        db_function_info = debuginfo.DebugFunction('main',
            common.SourceLocation('main.wasm', 1, 1, 1),
            db_float, ())
        debug_db.enter(ppci_function, db_function_info)

        entryblock = self.new_block()
        self.builder.set_block(entryblock)
        ppci_function.entry = entryblock

        self.localmap = {}
        for i, local in enumerate(wasm_function.locals):
            self.localmap[i] = self.emit(ir.Alloc(f'local{i}', 8))

        num = len(wasm_function.instructions)
        for nr, instruction in enumerate(wasm_function.instructions, start=1):
            inst = instruction.type
            self.logger.debug('%s/%s %s', nr, num, inst)
            self.generate_instruction(instruction)
        ppci_function.delete_unreachable()

    def generate_instruction(self, instruction):
        inst = instruction.type
        if inst in ('f64.add', 'f64.sub', 'f64.mul', 'f64.div'):
            itype, opname = inst.split('.')
            op = dict(add='+', sub='-', mul='*', div='/')[opname]
            b, a = self.stack.pop(), self.stack.pop()
            value = self.emit(ir.Binop(a, op, b, opname, self.get_ir_type(itype)))
            self.stack.append(value)

        elif inst in ('f64.eq', 'f64.ne', 'f64.ge', 'f64.gt', 'f64.le', 'f64.lt'):
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append((inst.split('.')[1], a, b))  # todo: hack; we assume this is the only test in an if
        elif inst == 'f64.floor':
            value1 = self.emit(ir.Cast(self.stack.pop(), 'floor_cast_1', ir.i64))
            value2 = self.emit(ir.Cast(value1, 'floor_cast_2', ir.f64))
            self.stack.append(value2)

        elif inst == 'f64.const':
            value = self.emit(ir.Const(instruction.args[0], 'const', self.get_ir_type(inst)))
            self.stack.append(value)

        elif inst == 'set_local':
            value = self.stack.pop()
            self.emit(ir.Store(value, self.localmap[instruction.args[0]]))

        elif inst == 'get_local':
            value = self.emit(ir.Load(self.localmap[instruction.args[0]], 'getlocal', self.get_ir_type(inst)))
            self.stack.append(value)

        elif inst == 'f64.neg':
            zero = self.emit(ir.Const(0, 'zero', self.get_ir_type(inst)))
            value = self.emit(ir.sub(zero, self.stack.pop(), 'neg', self.get_ir_type(inst)))
            self.stack.append(value)

        elif inst == 'block':
            innerblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.Jump(innerblock))
            self.builder.set_block(innerblock)
            self.block_stack.append(('block', continueblock, innerblock))

        elif inst == 'loop':
            innerblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.Jump(innerblock))
            self.builder.set_block(innerblock)
            self.block_stack.append(('loop', continueblock, innerblock))

        elif inst == 'br':
            depth = instruction.args[0]
            blocktype, continueblock, innerblock = self.block_stack[-depth-1]
            targetblock = innerblock if blocktype == 'loop' else continueblock
            self.emit(ir.Jump(targetblock))
            falseblock = self.new_block()  # unreachable
            self.builder.set_block(falseblock)

        elif inst == 'br_if':
            opmap = dict(eq='==', ne='!=', ge='>=', le='<=', gt='>', lt='<')
            op, a, b = self.stack.pop()
            depth = instruction.args[0]
            blocktype, continueblock, innerblock = self.block_stack[-depth-1]
            targetblock = innerblock if blocktype == 'loop' else continueblock
            falseblock = self.new_block()
            self.emit(ir.CJump(a, opmap[op], b, targetblock, falseblock))
            self.builder.set_block(falseblock)

        elif inst == 'if':
            # todo: we assume that the test is a comparison
            opmap = dict(ge='>=', le='<=', eq='==', gt='>', lt='<')
            op, a, b = self.stack.pop()
            trueblock = self.new_block()
            continueblock = self.new_block()
            self.emit(ir.CJump(a, opmap[op], b, trueblock, continueblock))
            self.builder.set_block(trueblock)
            self.block_stack.append(('if', continueblock))

        elif inst == 'else':
            blocktype, continueblock = self.block_stack.pop()
            assert blocktype == 'if'
            elseblock = continueblock  # continueblock becomes elseblock
            continueblock = self.new_block()
            self.emit(ir.Jump(continueblock))
            self.builder.set_block(elseblock)
            self.block_stack.append(('else', continueblock))

        elif inst == 'end':
            continueblock = self.block_stack.pop()[1]
            self.emit(ir.Jump(continueblock))
            self.builder.set_block(continueblock)

        elif inst == 'return':
            self.emit(ir.Return(self.stack.pop()))
            # after_return_block = self.new_block()
            # self.builder.set_block(after_return_block)
            # todo: assert that this was the last instruction

        else:  # pragma: no cover
            raise NotImplementedError(inst)

