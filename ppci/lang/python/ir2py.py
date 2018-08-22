""" Python back-end. Generates python code from ir-code. """

import io
import time
from ... import ir


def literal_label(lit):
    """ Invent a nice label name for the given literal """
    return '{}_{}'.format(lit.function.name, lit.name)


def ir_to_python(ir_modules, f, reporter=None):
    """ Convert ir-code to python code """
    if reporter:
        f2 = f
        f = io.StringIO()

    generator = IrToPythonCompiler(f)
    generator.header()
    for ir_module in ir_modules:
        generator.generate(ir_module)

    if reporter:
        source_code = f.getvalue()
        f2.write(source_code)
        reporter.dump_source('Python code', source_code)


class IrToPythonCompiler:
    """ Can generate python script from ir-code """
    def __init__(self, output_file):
        self.output_file = output_file
        self.stack_size = 0
        self.func_ptr_map = {}

    def print(self, level, *args):
        """ Print args to current file with level indents """
        print('    '*level, end='', file=self.output_file)
        print(*args, file=self.output_file)

    def header(self):
        self.print(0, '# Automatically generated on {}'.format(time.ctime()))
        self.print(0, '# Generator {}'.format(__file__))
        self.print(0, '')
        self.print(0, 'import struct')
        self.print(0, 'import math')
        self.print(0, '')
        self.print(0, 'heap = bytearray()')
        self.print(0, 'stack = bytearray()')
        self.print(0, 'HEAP_START = 0x10000000')
        self.print(0, 'func_pointers = list()')
        self.print(0, 'externals = {}')
        self.print(0, '')

        self.generate_builtins()
        self.generate_memory_builtins()

    def generate_memory_builtins(self):
        self.print(0, 'def read_mem(address, size):')
        self.print(1, 'mem, address = get_memory(address)')
        self.print(1, 'assert address+size <= len(mem), str(hex(address))')
        self.print(1, 'return mem[address:address+size]')
        self.print(0, '')

        self.print(0, 'def write_mem(address, data):')
        self.print(1, 'mem, address = get_memory(address)')
        self.print(1, 'size = len(data)')
        self.print(1, 'assert address+size <= len(mem), str(hex(address))')
        self.print(1, 'mem[address:address+size] = data')
        self.print(0, '')

        self.print(0, 'def get_memory(v):')
        self.print(1, 'if v >= HEAP_START:')
        self.print(2, 'return heap, v - HEAP_START')
        self.print(1, 'else:')
        self.print(2, 'return stack, v')
        self.print(0, '')

        self.print(0, 'def heap_top():')
        self.print(1, 'return len(heap) + HEAP_START')
        self.print(0, '')

        # Generate load functions:
        foo = [
            (ir.f64, 'd', 8),
            (ir.f32, 'f', 4),
            (ir.i64, 'q', 8),
            (ir.u64, 'Q', 8),
            (ir.i32, 'i', 4),
            (ir.u32, 'I', 4),
            (ir.ptr, 'i', 4),
            (ir.i16, 'h', 2),
            (ir.u16, 'H', 2),
            (ir.i8, 'b', 1),
            (ir.u8, 'B', 1),
            ]

        for ty, fmt, size in foo:
            # Generate load helpers:
            self.print(0, 'def load_{}(p):'.format(ty.name))
            self.print(
                1,
                'return struct.unpack("{0}", read_mem(p, {1}))[0]'.format(
                    fmt, size))
            self.print(0, '')

            # Generate store helpers:
            self.print(0, 'def store_{}(v, p):'.format(ty.name))
            self.print(
                1,
                'write_mem(p, struct.pack("{0}", v))'.format(fmt))
            self.print(0, '')

    def generate_builtins(self):
        # Wrap type helper:
        self.print(0, 'def correct(value, bits, signed):')
        self.print(1, 'base = 1 << bits')
        self.print(1, 'value %= base')
        self.print(1, 'if signed and value.bit_length() == bits:')
        self.print(2, 'return value - base')
        self.print(1, 'else:')
        self.print(2, 'return value')
        self.print(0, '')

        # Truncating integer divide
        self.print(0, 'def idiv(x, y):')
        self.print(1, 'return int(math.trunc(x/y))')
        self.print(0, '')

        # More c like remainder:
        self.print(0, 'def irem(x, y):')
        self.print(1, 'sign = x < 0')
        self.print(1, 'v = abs(x) % abs(y)')
        self.print(1, 'if sign:')
        self.print(2, 'return -v')
        self.print(1, 'else:')
        self.print(2, 'return v')
        self.print(0, '')

        # More c like shift left:
        self.print(0, 'def ishl(x, amount, bits):')
        self.print(1, 'amount = amount % bits')
        self.print(1, 'return x << amount')

        # More c like shift right:
        self.print(0, 'def ishr(x, amount, bits):')
        self.print(1, 'amount = amount % bits')
        self.print(1, 'return x >> amount')

        self.print(0, 'def _alloca(amount):')
        self.print(1, 'ptr = len(stack)')
        self.print(1, 'stack.extend(bytes(amount))')
        self.print(1, 'return (ptr, amount)')
        self.print(0, '')

        self.print(0, 'def _free(amount):')
        self.print(1, 'for _ in range(amount):')
        self.print(2, 'stack.pop()')
        self.print(0, '')

    def generate(self, ir_mod):
        """ Write ir-code to file f """
        self.mod_name = ir_mod.name
        self.literals = []
        self.print(0)
        self.print(0, '# Module {}'.format(ir_mod.name))
        # Allocate room for global variables:
        for var in ir_mod.variables:
            self.print(0, '{} = heap_top()'.format(var.name))
            if var.value:
                for byte in var.value:
                    self.print(0, 'heap.append({})'.format(byte))
            else:
                self.print(0, 'heap.extend(bytes({}))'.format(var.amount))

        # Generate functions:
        for function in ir_mod.functions:
            self.generate_function(function)

        # emit labeled literals:
        for lit in self.literals:
            self.print(0, "{} = heap_top()".format(literal_label(lit)))
            for val in lit.data:
                self.print(0, "heap.append({})".format(val))
        self.print(0)

    def generate_function(self, fn):
        """ Generate a function to python code """
        self.stack_size = 0
        args = ','.join(a.name for a in fn.arguments)
        self.print(0, 'def {}({}):'.format(fn.name, args))
        self.print(1, "prev_block = None")
        self.print(1, "current_block = '{}'".format(fn.entry.name))
        self.print(1, 'while True:')
        for block in fn.blocks:
            self.print(2, 'if current_block == "{}":'.format(block.name))
            for ins in block:
                self.generate_instruction(ins)
        self.print(0)

        # Register function for function pointers:
        self.print(0, 'func_pointers.append({})'.format(fn.name))
        self.func_ptr_map[fn] = len(self.func_ptr_map)
        self.print(0)

    def reset_stack(self, level):
        self.print(level, '_free({})'.format(self.stack_size))
        self.stack_size = 0

    def generate_instruction(self, ins):
        """ Generate python code for this instruction """
        if isinstance(ins, ir.CJump):
            self.print(3, 'if {} {} {}:'.format(
                ins.a.name, ins.cond, ins.b.name))
            self.print(4, 'prev_block = current_block')
            self.print(4, 'current_block = "{}"'.format(ins.lab_yes.name))
            self.print(3, 'else:')
            self.print(4, 'prev_block = current_block')
            self.print(4, 'current_block = "{}"'.format(ins.lab_no.name))
        elif isinstance(ins, ir.Jump):
            self.print(3, 'prev_block = current_block')
            self.print(3, 'current_block = "{}"'.format(ins.target.name))
        elif isinstance(ins, ir.Alloc):
            self.print(3, '{} = _alloca({})'.format(ins.name, ins.amount))
            self.stack_size += ins.amount
        elif isinstance(ins, ir.AddressOf):
            self.print(3, '{} = {}[0]'.format(ins.name, ins.src.name))
        elif isinstance(ins, ir.Const):
            self.print(3, '{} = {}'.format(ins.name, ins.value))
        elif isinstance(ins, ir.LiteralData):
            assert isinstance(ins.data, bytes)
            self.literals.append(ins)
            self.print(3, '{} = ({},{})'.format(
                ins.name, literal_label(ins), len(ins.data)))
        elif isinstance(ins, ir.Unop):
            op = ins.operation
            self.print(3, '{} = {}{}'.format(
                ins.name, op, ins.a.name))
            if ins.ty.is_integer:
                self.print(3, '{0} = correct({0}, {1}, {2})'.format(
                    ins.name, ins.ty.bits, ins.ty.signed))
        elif isinstance(ins, ir.Binop):
            # Assume int for now.
            op = ins.operation
            int_ops = {
                '/': 'idiv',
                '%': 'irem',
            }

            shift_ops = {
                '>>': 'ishr',
                '<<': 'ishl',
            }

            if op in int_ops and ins.ty.is_integer:
                fname = int_ops[op]
                self.print(3, '{} = {}({}, {})'.format(
                    ins.name, fname, ins.a.name, ins.b.name))
            elif op in shift_ops and ins.ty.is_integer:
                fname = shift_ops[op]
                self.print(3, '{} = {}({}, {}, {})'.format(
                    ins.name, fname, ins.a.name, ins.b.name, ins.ty.bits))
            else:
                self.print(3, '{} = {} {} {}'.format(
                    ins.name, ins.a.name, op, ins.b.name))
            if ins.ty.is_integer:
                self.print(3, '{0} = correct({0}, {1}, {2})'.format(
                    ins.name, ins.ty.bits, ins.ty.signed))
        elif isinstance(ins, ir.Cast):
            if ins.ty.is_integer:
                self.print(3, '{} = correct(int(round({})), {}, {})'.format(
                    ins.name, ins.src.name, ins.ty.bits, ins.ty.signed))
            elif ins.ty is ir.ptr:
                self.print(3, '{} = int(round({}))'.format(
                    ins.name, ins.src.name))
            elif ins.ty in [ir.f32, ir.f64]:
                self.print(3, '{} = float({})'.format(ins.name, ins.src.name))
            else:  # pragma: no cover
                raise NotImplementedError(str(ins))
        elif isinstance(ins, ir.Store):
            if isinstance(ins.value.ty, ir.BlobDataTyp):
                self.print(3, 'write_mem({0}, {1}, {2})'.format(
                    ins.address.name,
                    ins.value.ty.size,
                    ins.value.name))
            else:
                if isinstance(ins.value, ir.SubRoutine):
                    # Function pointer!
                    fidx = self.func_ptr_map[ins.value]
                    v = str(fidx)
                else:
                    v = ins.value.name
                self.print(3, 'store_{0}({2}, {1})'.format(
                    ins.value.ty.name, ins.address.name, v))
        elif isinstance(ins, ir.Load):
            if isinstance(ins.ty, ir.BlobDataTyp):
                self.print(3, '{0} = read_mem({1}, {2})'.format(
                    ins.name,
                    ins.address.name,
                    ins.ty.size))
            else:
                self.print(3, '{0} = load_{1}({2})'.format(
                    ins.name, ins.ty.name, ins.address.name))
        elif isinstance(ins, ir.FunctionCall):
            args = ', '.join(a.name for a in ins.arguments)
            self._fetch_callee(ins.callee)
            self.print(3, '{} = _fptr({})'.format(ins.name, args))
        elif isinstance(ins, ir.ProcedureCall):
            args = ', '.join(a.name for a in ins.arguments)
            self._fetch_callee(ins.callee)
            self.print(3, '_fptr({})'.format(args))
        elif isinstance(ins, ir.Phi):
            self.print(3, 'if False:')
            self.print(4, 'pass')
            for inp in ins.inputs:
                self.print(3, 'elif prev_block == "{}":'.format(inp.name))
                self.print(4, '{} = {}'.format(ins.name, ins.inputs[inp].name))
            self.print(3, 'else:')
            self.print(4, 'raise RuntimeError(str(prev_block))')
        elif isinstance(ins, ir.Return):
            self.reset_stack(3)
            self.print(3, 'return {}'.format(ins.result.name))
        elif isinstance(ins, ir.Exit):
            self.reset_stack(3)
            self.print(3, 'return')
        else:  # pragma: no cover
            self.print(3, '{}'.format(ins))
            raise NotImplementedError(str(type(ins)))

    def _fetch_callee(self, callee):
        """ Retrieves a callee and puts it into _fptr variable """
        if isinstance(callee, ir.SubRoutine):
            self.print(3, '_fptr = {}'.format(callee.name))
        elif isinstance(callee, ir.ExternalSubRoutine):
            self.print(3, '_fptr = {}'.format(callee.name))
            # self.print(3, '_fptr = externals["{}"]'.format(callee.name))
        else:
            self.print(3, '_fptr = func_pointers[{}]'.format(callee.name))
