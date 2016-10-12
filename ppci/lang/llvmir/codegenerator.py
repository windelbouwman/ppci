
import logging
from . import nodes
from ... import ir, irutils


class CodeGenerator:
    """ Transform llvm-ir into ppci-ir """
    logger = logging.getLogger('llvm-gen')

    def __init__(self):
        self.builder = irutils.Builder()
        self.val_map = {}
        self.forward = {}

    def generate(self, ll_module):
        """ Convert LLVM IR-module to ppci IR-module """
        assert isinstance(ll_module, nodes.Module)
        self.logger.debug('generating ir-code from llvm ir-code')
        self.logger.warning('ir code generation not functional yet')
        self.builder.module = ir.Module('TODO')
        for function in ll_module.functions:
            self.gen_function(function)
        return self.builder.module

    def gen_function(self, function):
        """ Generate code for an llvm function """
        self.logger.debug('generating ir-code for %s', function)
        ir_function = self.builder.new_procedure('b')
        self.builder.set_function(ir_function)
        return
        for basic_block in function.basic_blocks:
            block = self.builder.new_block()
            self.builder.set_block(block)
            for instruction in basic_block.instructions:
                self.gen_instruction(instruction)

    def gen_instruction(self, instruction):
        """ Transform an llvm instruction into the right ppci ir part """
        if isinstance(instruction, nodes.BinaryOperator):
            self.emit(ir.Binop())
        elif isinstance(instruction, nodes.AllocaInst):
            amount = data_layout.get_type_alloc_size(instruction.allocated_ty)
            name = instruction.name
            ir_ins = self.emit(ir.Alloc(name, amount))
            self.val_map[instruction] = ir_ins
        elif isinstance(instruction, nodes.GetElementPtrInst):
            ir_ins = self.get_val(instruction.ptr)
            # TODO
        elif isinstance(instruction, nodes.LoadInst):
            ptr = self.get_val(instruction.ptr)
            ir_ins = self.emit(ir.Load(ptr, name, ty))
            self.val_map[instruction] = ir_ins
        elif isinstance(instruction, nodes.StoreInst):
            val = self.get_val(instruction.val)
            ptr = self.get_val(instruction.ptr)
            self.emit(ir.Store(val, ptr))
        elif isinstance(instruction, nodes.InsertElementInst):
            raise NotImplementedError()
        elif isinstance(instruction, nodes.ExtractElementInst):
            raise NotImplementedError()
        elif isinstance(instruction, nodes.ShuffleVectorInst):
            raise NotImplementedError()
        elif isinstance(instruction, nodes.SelectInst):
            raise NotImplementedError()
        elif isinstance(instruction, nodes.PhiNode):
            phi = ir.Phi()
            for incoming in instruction:
                value = self.get_val()
                block = 1
                phi.set_incoming(block, value)
            self.emit(phi)
        elif isinstance(instruction, nodes.ICmpInst):
            block0 = self.builder.new_block()
            block1 = self.builder.new_block()
            final = self.builder.new_block()
            self.emit(ir.CJump(a, '=', b, block1, block0))
            self.builder.set_block(block0)
            zero = self.emit(ir.Const(0, 'zero', ir.i8))
            self.emit(ir.Jump(final))
            self.builder.set_block(block1)
            one = self.emit(ir.Const(1, 'one', ir.i8))
            self.emit(ir.Jump(final))
            self.builder.set_block(final)
            phi = ir.Phi('icmp', ir.i8)
            phi.set_incoming(block0, zero)
            phi.set_incoming(block1, one)
            self.emit(phi)
            self.val_map[instruction] = phi
        elif isinstance(instruction, nodes.BranchInst):
            if isinstance(instruction.op1, nodes.BasicBlock):
                # Unconditional jump:
                block = self.get_block(instruction.op1)
                self.emit(ir.Jump(block))
            else:
                # conditional jump:
                block1 = self.get_block(instruction.op1)
                block2 = self.get_block(instruction.op2)
                val = self.get_val(instruction.op3)
                one = self.emit(ir.Const(1, 'one', ir.i8))
                self.emit(ir.CJump(val, '==', one, block1, block2))
        elif isinstance(instruction, nodes.ReturnInst):
            self.emit(ir.Return())
        elif isinstance(instruction, nodes.CallInst):
            self.emit(ir.Call())
        else:  # pragma: no cover
            raise NotImplementedError(str(instruction))

    def get_val(self, llvm_val):
        val = self.val_map[llvm_val]
        return val

    def emit(self, instruction):
        self.builder.emit(instruction)
