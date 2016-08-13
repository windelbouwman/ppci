"""
    Python back-end. Generates python code from ir-code.
"""

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
        # Generate helper:
        self.print(0, 'def wrap_byte(v):')
        self.print(1, 'if v < 0:')
        self.print(2, 'v += 256')
        self.print(1, 'if v > 255:')
        self.print(2, 'v -= 256')
        self.print(1, 'return v')
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
            self.print(3, '{} = int({} {} {})'.format(
                ins.name, ins.a.name, ins.operation, ins.b.name))
            # Implement wrapping around zero:
            if ins.ty is ir.i8:
                self.print(3, '{0} = wrap_byte({0})'.format(ins.name))
        elif isinstance(ins, ir.Cast):
            self.print(3, '{} = {}'.format(ins.name, ins.src.name))
        elif isinstance(ins, ir.Store):
            store_formats = {
                ir.ptr: 'mem[{0}:{0}+4] = struct.pack("i",{1})',
                ir.i32: 'mem[{0}:{0}+4] = struct.pack("i",{1})',
                ir.i8: 'mem[{0}:{0}+1] = struct.pack("B",{1})'
            }
            fmt = store_formats[ins.value.ty]
            self.print(3, fmt.format(ins.address.name, ins.value.name))
        elif isinstance(ins, ir.Load):
            load_formats = {
                ir.i32: '{0}, = struct.unpack("i", mem[{1}:{1}+4])',
                ir.ptr: '{0}, = struct.unpack("i", mem[{1}:{1}+4])',
                ir.i8: '{0} = mem[{1}]'
            }
            fmt = load_formats[ins.ty]
            self.print(3, fmt.format(ins.name, ins.address.name))
        elif isinstance(ins, (ir.FunctionCall, ir.ProcedureCall)):
            self.print(3, '{}'.format(ins))
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
