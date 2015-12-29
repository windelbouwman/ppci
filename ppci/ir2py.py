"""
    Python back-end. Generates python code from ir-code.
"""

from . import ir


def literal_label(lit):
    """ Invent a nice label name for the given literal """
    return '{}_{}'.format(lit.function.name, lit.name)


class IrToPython:
    """ Can generate python script from ir-code """
    def __init__(self):
        self.f = None

    def print(self, level, *args):
        """ Print args to current file with level indents """
        print('    '*level, end='', file=self.f)
        print(*args, file=self.f)

    def header(self):
        self.print(0, 'import struct')
        self.print(0, '')
        self.print(0, 'mem = list()')
        # Generate helper:
        self.print(0, 'def wrap_byte(v):')
        self.print(1, 'if v < 0:')
        self.print(2, 'v += 256')
        self.print(1, 'if v > 255:')
        self.print(2, 'v -= 256')
        self.print(1, 'return v')
        self.print(0, '')

    def generate(self, ir_mod, f):
        """ Write ir-code to file f """
        self.f = f
        self.mod_name = ir_mod.name
        self.literals = []
        self.print(0, '')
        self.print(0, '# Module {}'.format(ir_mod.name))
        # Allocate room for global variables:
        for var in ir_mod.Variables:
            self.print(0, '{} = len(mem)'.format(var.name))
            self.print(0, 'mem.extend([0]*{})'.format(var.amount))

        # Generate functions:
        for function in ir_mod.Functions:
            self.generate_function(function)

        # emit labeled literals:
        for lit in self.literals:
            self.print(0, "{} = len(mem)".format(literal_label(lit)))
            for val in lit.data:
                self.print(0, "mem.append({})".format(val))
        self.print(0, '')

    def generate_function(self, fn):
        args = ','.join(a.name for a in fn.arguments)
        self.print(0, 'def {}_{}({}):'.format(self.mod_name, fn.name, args))
        self.print(1, "prev_block = None")
        self.print(1, "current_block = 'entry'")
        self.print(1, 'while True:')
        for block in fn.blocks:
            self.print(2, 'if current_block == "{}":'.format(block.name))
            for ins in block:
                self.generate_instruction(ins)
        self.print(0, '')

    def generate_instruction(self, ins):
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
        elif isinstance(ins, ir.Terminator):
            self.print(3, 'break')
        elif isinstance(ins, ir.Alloc):
            # TODO: strap stack on function exit.
            self.print(3, '{} = len(mem)'.format(ins.name))
            self.print(3, 'mem.extend([0]*{})'.format(ins.amount))
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
            # print(ins
            # TODO: improve this mess? Helper functions?
            if ins.value.ty is ir.i32 or ins.value.ty is ir.ptr:
                self.print(3, 'mem[{0}:{0}+4] = list(struct.pack("i",{1}))'
                           .format(ins.address.name, ins.value.name))
            elif ins.value.ty is ir.i8:
                self.print(3, 'mem[{0}:{0}+1] = list(struct.pack("B",{1}))'
                           .format(ins.address.name, ins.value.name))
            else:  # pragma: no cover
                raise NotImplementedError()
        elif isinstance(ins, ir.Load):
            if ins.ty is ir.i8:
                self.print(
                    3, '{} = mem[{}]'.format(ins.name, ins.address.name))
            elif ins.ty is ir.i32 or ins.ty is ir.ptr:
                self.print(
                    3, '{0}, = struct.unpack("i", bytes(mem[{1}:{1}+4]))'
                    .format(ins.name, ins.address.name))
            else:  # pragma: no cover
                raise NotImplementedError()
        elif isinstance(ins, ir.Call):
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
            self.print(3, 'return {}'.format(ins.result.name))
        else:  # pragma: no cover
            self.print(3, '{}'.format(ins))
            raise NotImplementedError()
