
import logging
from . import nodes
from ... import ir, irutils


class CodeGenerator:
    logger = logging.getLogger('llvm-gen')

    def __init__(self):
        self.builder = irutils.Builder()
        self.val_map = {}

    def generate(self, module):
        """ Convert LLVM IR-module to ppci IR-module """
        assert isinstance(module, nodes.Module)
        self.logger.debug('generating ir-code from llvm ir-code')
        self.logger.warning('ir code generation not functional yet')
        self.builder.module = ir.Module('TODO')
        for function in module.functions:
            self.gen_function(function)
        return self.builder.module

    def gen_function(self, function):
        """ Generate code for an llvm function """
        self.logger.debug('generating ir-code for %s', function)
        return
        ir_function = self.builder.new_procedure('b')
        self.builder.set_function(ir_function)
        for basic_block in function.basic_blocks:
            block = self.builder.new_block()
            self.builder.set_block(block)
            for instruction in basic_block.instructions:
                self.gen_instruction(instruction)

    def gen_instruction(self, instruction):
        if isinstance(instruction, nodes.BinaryOperator):
            self.emit(ir.Binop())
        elif isinstance(instruction, nodes.AllocaInst):
            amount = data_layout.get_type_alloc_size(instruction.allocated_ty)
            name = instruction.name
            ir_ins = self.emit(ir.Alloc(name, amount))
            self.val_map[instruction] = ir_ins
        elif isinstance(instruction, nodes.GetElementPtrInst):
            ir_ins = self.val_map[instruction.ptr]
            # TODO
        elif isinstance(instruction, nodes.LoadInst):
            ptr = self.val_map[instruction.ptr]
            ir_ins = self.emit(ir.Load(ptr, name, ty))
            self.val_map[instruction] = ir_ins
        elif isinstance(instruction, nodes.StoreInst):
            val = self.val_map[instruction.val]
            ptr = self.val_map[instruction.ptr]
            ir_ins = self.emit(ir.Store(ptr, name, ty))
            self.val_map[instruction] = ir_ins
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))

    def emit(self, instruction):
        self.builder.emit(instruction)
