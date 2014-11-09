
"""
    This is the brain-fuck language front-end.
"""

import logging

from . import ir
from .irutils import Builder


class BrainFuckGenerator():
    """ Brainfuck is a language that is so simple, the entire front-end can
    be implemented in one pass.
    """
    def __init__(self):
        self.logger = logging.getLogger('bfgen')
        self.builder = Builder()

    def generate(self, src, module_name='sample'):
        """ Takes a brainfuck program and returns the IR-code module """
        self.logger.info('Generating IR-code from brainfuck')

        # Assembler code will call sample_start
        self.builder.m = ir.Module(module_name)

        ir_func = self.builder.new_function('start')
        self.builder.setFunction(ir_func)

        block1 = self.builder.newBlock()
        self.builder.emit(ir.Jump(block1))
        self.builder.setBlock(block1)

        # Allocate space on stack for ptr register:
        ptr_var = self.builder.emit(ir.Alloc('ptr_addr', ir.i32))

        # Construct global array:
        array_type = ir.ArrayType(ir.i32, 30000)
        data = ir.Variable('data', array_type)
        self.builder.m.add_variable(data)

        # Locate '1' and '0' constants:
        one_ins = self.builder.emit(ir.Const(1, "one", ir.i32))
        four_ins = self.builder.emit(ir.Const(4, "four", ir.i32))
        zero_ins = self.builder.emit(ir.Const(0, "zero", ir.i32))
        array_size = self.builder.emit(ir.Const(1000, "array_max", ir.i32))

        # Store initial value of ptr:
        self.builder.emit(ir.Store(zero_ins, ptr_var))

        # Initialize array to zero:
        block3 = self.builder.newBlock()
        block_init = self.builder.newBlock()
        self.builder.emit(ir.Jump(block_init))

        self.builder.setBlock(block_init)
        ptr_val = self.builder.emit(ir.Load(ptr_var, "ptr_val", ir.i32))
        cell_addr = self.builder.emit(ir.Add(data, ptr_val, "cell_addr", ir.i32))
        self.builder.emit(ir.Store(zero_ins, cell_addr))
        add_ins = self.builder.emit(ir.Add(ptr_val, four_ins, "Added", ir.i32))
        self.builder.emit(ir.Store(add_ins, ptr_var))
        self.builder.emit(ir.CJump(add_ins, '==', array_size, block3, block_init))

        self.builder.setBlock(block3)

        # Start with ptr as zero:
        ptr = zero_ins

        # A stack of all nested loops:
        loops = []

        # A mapping of all loop entries to the phi functions of ptr:
        phi_map = {}

        # Cached copy of cell address calculation:
        cell_addr = None

        # Implement all instructions:
        for c in src:
            if c == '>':
                # ptr++;
                ptr = self.builder.emit(ir.Add(ptr, four_ins, "ptr", ir.i32))
                cell_addr = None
            elif c == '<':
                # ptr--;
                ptr = self.builder.emit(ir.Sub(ptr, four_ins, "ptr", ir.i32))
                cell_addr = None
            elif c == '+':
                # data[ptr]++;
                if cell_addr is None:
                    cell_addr = self.builder.emit(ir.Add(data, ptr, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                add_ins = self.builder.emit(ir.Add(val_ins, one_ins, "Added", ir.i32))
                self.builder.emit(ir.Store(add_ins, cell_addr))
            elif c == '-':
                # data[ptr]--;
                if cell_addr is None:
                    cell_addr = self.builder.emit(ir.Add(data, ptr, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                sub_ins = self.builder.emit(ir.Sub(val_ins, one_ins, "Sub", ir.i32))
                self.builder.emit(ir.Store(sub_ins, cell_addr))
            elif c == '.':
                # putc(data[ptr])
                if cell_addr is None:
                    cell_addr = self.builder.emit(ir.Add(data, ptr, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                self.builder.emit(ir.Call('arch_putc', [val_ins], 'ign', ir.i32))
            elif c == ',':
                # data[ptr] = getchar()
                raise NotImplementedError('"," operator not implemented')
            elif c == '[':
                entry = self.builder.newBlock()
                body = self.builder.newBlock()
                exit = self.builder.newBlock()
                current_block = self.builder.block

                # Register phi node into entry:
                ptr_phi = ir.Phi('ptr_phi', ir.i32)
                ptr_phi.set_incoming(current_block, ptr)
                phi_map[entry] = ptr_phi

                # Jump to entry:
                self.builder.emit(ir.Jump(entry))
                self.builder.setBlock(entry)

                # Register the phi node:
                self.builder.emit(ptr_phi)
                ptr = ptr_phi

                # Create test, jump to exit when *ptr == 0:
                cell_addr = self.builder.emit(ir.Add(data, ptr, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                self.builder.emit(ir.CJump(val_ins, '==', zero_ins, exit, body))

                # Set body as current block:
                self.builder.setBlock(body)
                loops.append((entry, exit))
            elif c == ']':
                # Invalidate local copy of cell address:
                cell_addr = None

                # Jump back to condition code:
                entry, exit = loops.pop(-1)

                # Set incoming branch to phi node:
                current_block = self.builder.block
                ptr_phi = phi_map[entry]
                ptr_phi.set_incoming(current_block, ptr)

                # Jump to entry again:
                self.builder.emit(ir.Jump(entry))
                self.builder.setBlock(exit)

                # Set ptr to phi value front entry:
                ptr = ptr_phi
            else:
                pass
        if loops:
            raise Exception('[ requires matching ]')

        # Jump to end of function:
        self.builder.emit(ir.Jump(ir_func.epiloog))

        # Yield module
        return self.builder.m
