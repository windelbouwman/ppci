
"""
    This is the brain-fuck language front-end.
"""

import logging

from . import ir
from .irutils import Builder


class BrainFuckGenerator():
    """ Brainfuck is a language that is so simple, the entire front-end can
    be implemented in one pass
    """
    def __init__(self):
        self.logger = logging.getLogger('bfgen')
        self.builder = Builder()

    def generate(self, src):
        self.logger.info('Generating IR-code from brainfuck')

        # Assembler code will call sample_start
        self.builder.m = ir.Module('sample')

        ir_func = self.builder.new_function('start')
        self.builder.setFunction(ir_func)

        block1 = self.builder.newBlock()
        self.builder.emit(ir.Jump(block1))
        self.builder.setBlock(block1)

        # Allocate space on stack for ptr register:
        ptr = self.builder.emit(ir.Alloc('ptr_addr', ir.i32))

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
        self.builder.emit(ir.Store(zero_ins, ptr))

        # Initialize array to zero:
        block3 = self.builder.newBlock()
        block_init = self.builder.newBlock()
        self.builder.emit(ir.Jump(block_init))

        self.builder.setBlock(block_init)
        ptr_val = self.builder.emit(ir.Load(ptr, "ptr_val", ir.i32))
        cell_addr = self.builder.emit(ir.Add(data, ptr_val, "cell_addr", ir.i32))
        self.builder.emit(ir.Store(zero_ins, cell_addr))
        add_ins = self.builder.emit(ir.Add(ptr_val, four_ins, "Added", ir.i32))
        self.builder.emit(ir.Store(add_ins, ptr))

        # Emit B: (for printf style debug purpose)
        # charBins = self.builder.emit(ir.Const(66, "charB", ir.i32))
        # self.builder.emit(ir.Call('arch_putc', [charBins], 'ign', ir.i32))

        self.builder.emit(ir.CJump(add_ins, '==', array_size, block3, block_init))

        self.builder.setBlock(block3)
        # Store initial value of ptr:
        self.builder.emit(ir.Store(zero_ins, ptr))

        # Implement all instructions:
        loops = []
        for c in src:
            if c == '>':
                # ptr++;
                load_ins = self.builder.emit(ir.Load(ptr, "ptr_val", ir.i32))
                add_ins = self.builder.emit(ir.Add(load_ins, four_ins, "Added", ir.i32))
                self.builder.emit(ir.Store(add_ins, ptr))
            elif c == '<':
                # ptr--;
                load_ins = self.builder.emit(ir.Load(ptr, "ptr_val", ir.i32))
                add_ins = self.builder.emit(ir.Sub(load_ins, four_ins, "Substracted", ir.i32))
                self.builder.emit(ir.Store(add_ins, ptr))
            elif c == '+':
                # data[ptr]++;
                load_ins = self.builder.emit(ir.Load(ptr, "ptr", ir.i32))
                cell_addr = self.builder.emit(ir.Add(data, load_ins, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                add_ins = self.builder.emit(ir.Add(val_ins, one_ins, "Added", ir.i32))
                self.builder.emit(ir.Store(add_ins, cell_addr))
            elif c == '-':
                # data[ptr]--;
                load_ins = self.builder.emit(ir.Load(ptr, "ptr", ir.i32))
                cell_addr = self.builder.emit(ir.Add(data, load_ins, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                sub_ins = self.builder.emit(ir.Sub(val_ins, one_ins, "Sub", ir.i32))
                self.builder.emit(ir.Store(sub_ins, cell_addr))
                pass
            elif c == '.':
                # putc(data[ptr])
                load_ins = self.builder.emit(ir.Load(ptr, "ptr", ir.i32))
                cell_addr = self.builder.emit(ir.Add(data, load_ins, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                self.builder.emit(ir.Call('arch_putc', [val_ins], 'ign', ir.i32))
            elif c == ',':
                # data[ptr] = getchar()
                # TODO
                pass
            elif c == '[':
                entry = self.builder.newBlock()
                body = self.builder.newBlock()
                exit = self.builder.newBlock()

                # Jump to entry:
                self.builder.emit(ir.Jump(entry))
                self.builder.setBlock(entry)

                # Create test, jump to exit when *ptr == 0:
                load_ins = self.builder.emit(ir.Load(ptr, "ptr", ir.i32))
                cell_addr = self.builder.emit(ir.Add(data, load_ins, "cell_addr", ir.i32))
                val_ins = self.builder.emit(ir.Load(cell_addr, "ptr_val", ir.i32))
                self.builder.emit(ir.CJump(val_ins, '==', zero_ins, exit, body))

                # Set body as current block:
                self.builder.setBlock(body)
                loops.append((entry, exit))
            elif c == ']':
                # Jump back to condition code:
                entry, exit = loops.pop(-1)
                self.builder.emit(ir.Jump(entry))
                self.builder.setBlock(exit)
            else:
                pass
        if loops:
            raise Exception('[ requires matching ]')

        # Jump to end of function:
        self.builder.emit(ir.Jump(ir_func.epiloog))

        # Yield module
        return self.builder.m
