
from . import ir


class IrToPython:
    """ Can generate python script from ir-code """
    def __init__(self):
        self.f = None

    def print(self, level, *args):
        """ Print args to current file with level indents """
        print('    '*level, end='', file=self.f)
        print(*args, file=self.f)

    def header(self):
        self.print(0, 'mem = list()')

    def generate(self, ir_mod, f):
        """ Write ir-code to file f """
        self.f = f
        self.mod_name = ir_mod.name
        self.string_literals = []
        self.print(0, '')
        self.print(0, '# Module {}'.format(ir_mod.name))
        # Allocate room for global variables:
        for var in ir_mod.Variables:
            self.print(0, '{} = len(mem)'.format(var.name))
            self.print(0, 'mem.extend([0]*{})'.format(var.ty.size))

        # Generate functions:
        for function in ir_mod.Functions:
            self.generate_function(function)

        # TODO: fix this mess with string literals
        for lit in self.string_literals:
            self.print(0, "{}_{} = len(mem)".format(
                lit.function.name, lit.name))
            for val in lit.value:
                self.print(0, "mem.append({})".format(val))

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
            if type(ins.value) is bytes:
                self.string_literals.append(ins)
            else:
                self.print(3, '{} = {}'.format(ins.name, ins.value))
        elif isinstance(ins, ir.Binop):
            self.print(3, '{} = {} {} {}'.format(
                ins.name, ins.a.name, ins.operation, ins.b.name))
        elif isinstance(ins, ir.Store):
            self.print(3, 'mem[{}] = {}'
                       .format(ins.address.name, ins.value.name))
        elif isinstance(ins, ir.Load):
            self.print(3, '{} = mem[{}]'.format(ins.name, ins.address.name))
        elif isinstance(ins, ir.Call):
            self.print(3, '{}'.format(ins))
        elif isinstance(ins, ir.Addr):
            # This is only used for string constants.
            # TODO: fix string literals better
            assert type(ins.e.value) is bytes
            self.print(3, '{} = {}_{}'.format(
                ins.name, ins.function.name, ins.e.name))
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
        else:
            self.print(3, '{}'.format(ins))
            raise NotImplementedError()
