# WIP
from ... import ir, relooper
from . import components
from ...domtree import CfgInfo


def ir_to_wasm(ir_module):
    c = IrToWasmConvertor()
    return c.do(ir_module)


class Gen:
    def __init__(self, loops):
        self.loop = 0
        self.loops = loops

    def gen_block(self, block):
        print('  ' * self.loop + str(block))
        # for s in block.successors:
            # self.gen_block(s)


class IrToWasmConvertor:
    """ Translates ir-code into wasm """
    def __init__(self):
        pass

    def do(self, ir_module):
        self.sections = []
        for ir_function in ir_module.functions:
            self.do_function(ir_function)

        wasm_module = components.Module(
            *self.sections
        )
        return wasm_module

    def do_function(self, ir_function):
        """ Generate WASM for a single function """
        function_name = ir_function.name
        self.instructions = []
        self.local_var_map = {}
        self.local_vars = []
        print()
        print('function:', ir_function)
        cfg = CfgInfo(ir_function)
        print('dominance tree', cfg.root_tree)

        # Loop info:
        loops = cfg.calc_loops()
        print('Loops', loops)
        # print('Dominance frontier', cfg.df)
        # TODO: use the relooper algorithm to construct a structured
        # flow graph
        print()
        # g = Gen(loops)
        # g.gen_block(function.entry)

        # Store incoming arguments:
        for argument in reversed(ir_function.arguments):
            self.emit(('set_local', self.get_value(argument)))

        # Emulated block jumps!
        #self.emit(('loop',))
        #self.emit(('block',))
        # self.emit(('br_table',))  # TODO: branch to the proper block
        for ir_block in ir_function:
            self.do_block(ir_block)
        #self.emit(('end',))

        # Determine function signature:
        arg_types = [self.get_ty(a.ty) for a in ir_function.arguments]
        if isinstance(ir_function, ir.Function):
            ret_types = [self.get_ty(ir_function.return_ty)]
        else:
            ret_types = []

        self.sections.append(components.Function(
            function_name, arg_types, ret_types, self.local_vars,
            self.instructions))

    def do_block(self, block):
        for instruction in block:
            self.do_instruction(instruction)

    def do_instruction(self, ir_instruction):
        if isinstance(ir_instruction, ir.Binop):
            op_map = {
                '+': 'add',
                '-': 'sub',
                '/': 'div',
                '*': 'mul',
                '%': 'mod',
            }
            if ir_instruction.operation in op_map:
                self.emit(('get_local', self.get_value(ir_instruction.a)))
                self.emit(('get_local', self.get_value(ir_instruction.b)))
                opcode = op_map[ir_instruction.operation]
                ty = self.get_ty(ir_instruction.ty)
                self.emit(('{}.{}'.format(ty, opcode), ))
                self.emit(('set_local', self.get_value(ir_instruction)))
            else:
                raise NotImplementedError(str(ir_instruction))
        elif isinstance(ir_instruction, ir.Alloc):
            heap = 0
            heap += ir_instruction.amount
            self.emit(('set_local', 'heap', heap))
        elif isinstance(ir_instruction, ir.Store):
            self.emit(('store.i64', self.get_value(ir_instruction.value)))
        elif isinstance(ir_instruction, ir.Load):
            self.emit(('load.i64', ))
            self.emit(('set_local', self.get_value(ir_instruction)))
        elif isinstance(ir_instruction, ir.Exit):
            self.emit(('return',))
        elif isinstance(ir_instruction, ir.Return):
            self.emit(('get_local', self.get_value(ir_instruction.result)))
            self.emit(('return',))
        elif isinstance(ir_instruction, ir.Const):
            ty = self.get_ty(ir_instruction.ty)
            self.emit(('{}.const'.format(ty), ir_instruction.value))
            self.emit(('set_local', self.get_value(ir_instruction)))
        elif isinstance(ir_instruction, ir.Cast):
            self.emit(('get_local', self.get_value(ir_instruction.src)))
            self.emit(('set_local', self.get_value(ir_instruction)))
        elif isinstance(ir_instruction, ir.ProcedureCall):
            for argument in ir_instruction.arguments:
                self.emit(('get_local', self.get_value(argument)))
            self.emit(('call', ir_instruction.function.name))
        elif isinstance(ir_instruction, ir.FunctionCall):
            for argument in ir_instruction.arguments:
                self.emit(('get_local', self.get_value(argument)))
            self.emit(('call', ir_instruction.function.name))
            self.emit(('set_local', self.get_value(ir_instruction)))
        elif isinstance(ir_instruction, ir.Jump):
            # TODO!
            block = ir_instruction.block
            self.fill_phis(block, ir_instruction.target)
            self.emit(('break', ))
        elif isinstance(ir_instruction, ir.CJump):
            # TODO!
            block = ir_instruction.block
            self.emit(('if', ))
            self.fill_phis(block, ir_instruction.lab_yes)
            self.emit(('else', ))
            self.fill_phis(block, ir_instruction.lab_no)
            self.emit(('end', ))
            self.emit(('break', ))
        elif isinstance(ir_instruction, ir.Phi):
            # Phi nodes are handled in jumps to this block!
            pass
        else:
            raise NotImplementedError(str(ir_instruction))

    def fill_phis(self, from_block, to_block):
        for i in to_block:
            if isinstance(i, ir.Phi):
                v = i.get_value(from_block)
                self.emit(('get_local', self.get_value(v)))
                self.emit(('set_local', self.get_value(i)))

    def get_ty(self, ir_ty):
        ty_map = {
            ir.i8: 'i32',
            ir.i16: 'i32',
            ir.i32: 'i32',
            ir.i64: 'i64',
            ir.f64: 'f64',
        }
        return ty_map[ir_ty]

    def get_value(self, value):
        """ Create a local number for the given value """
        if value not in self.local_var_map:
            self.local_var_map[value] = len(self.local_var_map)
            ty = self.get_ty(value.ty)
            self.local_vars.append(ty)
        return self.local_var_map[value]

    def emit(self, instruction):
        print(instruction)
        self.instructions.append(instruction)
