""" Python back-end. Generates python code from ir-code. """

import time
from ... import ir


def literal_label(lit):
    """ Invent a nice label name for the given literal """
    return '{}_{}'.format(lit.function.name, lit.name)


def ir_to_python(ir_modules, f, reporter=None):
    """ Convert ir-code to python code """
    generator = IrToPythonTranspiler(f)
    generator.header()
    for ir_module in ir_modules:
        generator.generate(ir_module)


class IrToPythonTranspiler:
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
        self.print(0, '')
        self.print(0, 'mem = bytearray()')
        self.print(0, 'func_pointers = list()')
        self.print(0, '')

        self.generate_builtins()

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
                'return struct.unpack("{0}", mem[p:p+{1}])[0]'.format(
                    fmt, size))
            self.print(0, '')

            # Generate store helpers:
            self.print(0, 'def store_{}(v, p):'.format(ty.name))
            self.print(
                1,
                'mem[p:p+{1}] = struct.pack("{0}", v)'.format(fmt, size))
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

        self.print(0, 'def _alloc(amount):')
        self.print(1, 'ptr = len(mem)')
        self.print(1, 'mem.extend(bytes(amount))')
        self.print(1, 'return (ptr, amount)')
        self.print(0, '')

        self.print(0, 'def _free(amount):')
        self.print(1, 'for _ in range(amount):')
        self.print(2, 'mem.pop()')
        self.print(0, '')

    def generate(self, ir_mod):
        """ Write ir-code to file f """
        self.mod_name = ir_mod.name
        self.literals = []
        self.print(0)
        self.print(0, '# Module {}'.format(ir_mod.name))
        # Allocate room for global variables:
        for var in ir_mod.variables:
            self.print(0, '{} = len(mem)'.format(var.name))
            if var.value:
                for byte in var.value:
                    self.print(0, 'mem.append({})'.format(byte))
            else:
                self.print(0, 'mem.extend(bytes({}))'.format(var.amount))

        # Generate functions:
        for function in ir_mod.functions:
            self.generate_function(function)

        # emit labeled literals:
        for lit in self.literals:
            self.print(0, "{} = len(mem)".format(literal_label(lit)))
            for val in lit.data:
                self.print(0, "mem.append({})".format(val))
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
            self.print(3, '{} = _alloc({})'.format(ins.name, ins.amount))
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
            if op == '/' and ins.ty.is_integer:
                op = '//'
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
                self.print(3, 'mem[{0}:{0}+{1}] = {2}'.format(
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
                self.print(3, '{0} = mem[{1}:{1}+{2}]'.format(
                    ins.name,
                    ins.address.name,
                    ins.ty.size))
            else:
                self.print(3, '{0} = load_{1}({2})'.format(
                    ins.name, ins.ty.name, ins.address.name))
        elif isinstance(ins, ir.FunctionCall):
            args = ', '.join(a.name for a in ins.arguments)
            self.print(3, '{} = {}({})'.format(
                ins.name, ins.function_name, args))
        elif isinstance(ins, ir.FunctionPointerCall):
            args = ', '.join(a.name for a in ins.arguments)
            if isinstance(ins.function_ptr, ir.SubRoutine):
                self.print(3, '_fptr = {}'.format(ins.function_ptr.name))
            else:
                self.print(3, '_fptr = func_pointers[{}]'.format(
                    ins.function_ptr.name))
            self.print(3, '{} = _fptr({})'.format(ins.name, args))
        elif isinstance(ins, ir.ProcedureCall):
            args = ', '.join(a.name for a in ins.arguments)
            self.print(3, '{}({})'.format(ins.function_name, args))
        elif isinstance(ins, ir.ProcedurePointerCall):
            args = ', '.join(a.name for a in ins.arguments)
            if isinstance(ins.function_ptr, ir.SubRoutine):
                self.print(3, '_fptr = {}'.format(ins.function_ptr.name))
            else:
                self.print(3, '_fptr = func_pointers[{}]'.format(
                    ins.function_ptr.name))
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
