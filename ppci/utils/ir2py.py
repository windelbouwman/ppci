""" Python back-end. Generates python code from ir-code. """

from .. import ir


def literal_label(lit):
    """ Invent a nice label name for the given literal """
    return '{}_{}'.format(lit.function.name, lit.name)


class IrToPython:
    """ Can generate python script from ir-code """
    def __init__(self, output_file):
        self.output_file = output_file
        self.stack_size = 0

    def print(self, level, *args):
        """ Print args to current file with level indents """
        print('    '*level, end='', file=self.output_file)
        print(*args, file=self.output_file)

    def header(self):
        self.print(0, 'import struct')
        self.print(0, '')
        self.print(0, 'mem = bytearray()')

        # Wrap type helper:
        self.print(0, 'def correct(value, bits, signed):')
        self.print(1, 'base = 1 << bits')
        self.print(1, 'value %= base')
        self.print(1, 'if signed and value.bit_length() == bits:')
        self.print(2, 'return value - base')
        self.print(1, 'else:')
        self.print(2, 'return value')

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
        self.print(0, 'def {}_{}({}):'.format(self.mod_name, fn.name, args))
        self.print(1, "prev_block = None")
        self.print(1, "current_block = '{}'".format(fn.entry.name))
        self.print(1, 'while True:')
        for block in fn.blocks:
            self.print(2, 'if current_block == "{}":'.format(block.name))
            for ins in block:
                self.generate_instruction(ins)
        self.print(0)
        self.print(0)

    def reset_stack(self, level):
        while self.stack_size > 0:
            self.stack_size -= 1
            self.print(level, 'mem.pop()')

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
            self.print(3, '{} = len(mem)'.format(ins.name))
            self.print(3, 'mem.extend(bytes({}))'.format(ins.amount))
            self.stack_size += ins.amount
        elif isinstance(ins, ir.Const):
            self.print(3, '{} = {}'.format(ins.name, ins.value))
        elif isinstance(ins, ir.LiteralData):
            assert isinstance(ins.data, bytes)
            self.literals.append(ins)
            self.print(3, '{} = {}'.format(ins.name, literal_label(ins)))
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
            else:
                raise NotImplementedError(str(ins))
        elif isinstance(ins, ir.Store):
            store_formats = {
                ir.f64: 'mem[{0}:{0}+8] = struct.pack("d",{1})',
                ir.f32: 'mem[{0}:{0}+4] = struct.pack("f",{1})',
                ir.ptr: 'mem[{0}:{0}+4] = struct.pack("i",{1})',
                ir.i32: 'mem[{0}:{0}+4] = struct.pack("i",{1})',
                ir.u32: 'mem[{0}:{0}+4] = struct.pack("I",{1})',
                ir.i16: 'mem[{0}:{0}+2] = struct.pack("h",{1})',
                ir.u16: 'mem[{0}:{0}+2] = struct.pack("H",{1})',
                ir.i8: 'mem[{0}:{0}+1] = struct.pack("b",{1})',
                ir.u8: 'mem[{0}:{0}+1] = struct.pack("B",{1})',
            }
            fmt = store_formats[ins.value.ty]
            self.print(3, fmt.format(ins.address.name, ins.value.name))
        elif isinstance(ins, ir.Load):
            load_formats = {
                ir.f64: '{0}, = struct.unpack("d", mem[{1}:{1}+8])',
                ir.f32: '{0}, = struct.unpack("f", mem[{1}:{1}+4])',
                ir.i32: '{0}, = struct.unpack("i", mem[{1}:{1}+4])',
                ir.u32: '{0}, = struct.unpack("I", mem[{1}:{1}+4])',
                ir.ptr: '{0}, = struct.unpack("i", mem[{1}:{1}+4])',
                ir.i16: '{0}, = struct.unpack("h", mem[{1}:{1}+2])',
                ir.u16: '{0}, = struct.unpack("H", mem[{1}:{1}+2])',
                ir.i8: '{0}, = struct.unpack("b", mem[{1}:{1}+1])',
                ir.u8: '{0}, = struct.unpack("B", mem[{1}:{1}+1])',
            }
            fmt = load_formats[ins.ty]
            self.print(3, fmt.format(ins.name, ins.address.name))
        elif isinstance(ins, ir.FunctionCall):
            args = ', '.join(a.name for a in ins.arguments)
            self.print(3, '{} = {}({})'.format(
                ins.name, ins.function_name, args))
        elif isinstance(ins, ir.ProcedureCall):
            args = ', '.join(a.name for a in ins.arguments)
            self.print(3, '{}({})'.format(ins.function_name, args))
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
            raise NotImplementedError()
