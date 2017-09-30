from ... import ir, relooper
from . import components
from ...domtree import CfgInfo


def ir_to_wasm(ir_module):
    """ Compiles ir-code to a wasm module.

    Args:
        ir_module (ir.Module): The ir-module to compile

    Returns:
        A wasm module.
    """
    c = IrToWasmCompiler()
    return c.compile(ir_module)


class IrToWasmCompiler:
    """ Translates ir-code into wasm """
    def __init__(self):
        pass

    def compile(self, ir_module):
        """ Compile an ir-module into a wasm module """
        self.types = []
        self.exports = []
        self.functions = []
        self.function_defs = []
        self.function_ids = {}

        for ir_function in ir_module.functions:
            self.do_function(ir_function)

        wasm_module = components.Module(
            components.TypeSection(*self.types),
            components.FunctionSection(*self.functions),
            components.ExportSection(*self.exports),
            components.CodeSection(*self.function_defs),
        )
        return wasm_module

    def do_function(self, ir_function):
        """ Generate WASM for a single function """
        function_name = ir_function.name
        self.instructions = []
        self.local_var_map = {}
        self.local_vars = []
        self.block_nrs = {}
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
        # Locals are located in local 0, 1, 2 etc..
        for argument in ir_function.arguments:
            # Arguments are implicit locals
            self.get_value(argument)
        #    self.emit(('set_local', self.get_value(argument)))

        # Loop 
        self.block_idx_var = self.get_value(ir.Const(1, 'labelidx', ir.i32))
        self.emit(('i32.const', 0))
        self.emit(('set_local', self.block_idx_var))

        # Emulated block jumps!
        self.emit(('block', 'emptyblock'))  # Outer block, breaks to end
        self.emit(('loop', 'emptyblock'))  # Loop block, breaks to here.

        depth = 0
        for ir_block in ir_function:
            self.emit(('block', 'emptyblock'))
            self.block_nrs[ir_block] = depth
            depth += 1

        # branch to the proper block by br_table-ing to the right exit
        self.emit(('block', 'emptyblock'))
        self.emit(('get_local', self.block_idx_var))
        self.emit(('br_table', *list(range(depth)), 0))
        self.emit(('end',))

        for ir_block in ir_function:
            self.do_block(ir_block)
            self.emit(('br', depth))  # Branch to loop
            depth -= 1
            self.emit(('end',))

        self.emit(('end',))
        self.emit(('end',))

        # Determine function signature:
        arg_types = [self.get_ty(a.ty) for a in ir_function.arguments]
        if isinstance(ir_function, ir.Function):
            ret_types = [self.get_ty(ir_function.return_ty)]
            # Insert dummy value
            self.emit((ret_types[0] + '.const', 1))
        else:
            ret_types = []

        nr = len(self.types)
        self.function_ids[function_name] = nr
        self.types.append(components.FunctionSig(arg_types, ret_types))

        # Add function type-id:
        self.functions.append(nr)

        self.function_defs.append(components.FunctionDef(
            self.local_vars,
            *self.instructions))

        # Create an export section:
        self.exports.append(components.Export(function_name, 'function', nr))

    def do_block(self, block):
        for instruction in block:
            self.do_instruction(instruction)

    def do_instruction(self, ir_instruction):
        """ Implement proper logic for an ir instruction """
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
            # Another option might be branching out of all blocks?
            # nr = self.block_nrs[ir_instruction.block]
            # self.emit(('br', nr + 2))
        elif isinstance(ir_instruction, ir.Return):
            self.emit(('get_local', self.get_value(ir_instruction.result)))
            # nr = self.block_nrs[ir_instruction.block]
            # self.emit(('br', nr + 2))
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
            func_id = self.function_ids[ir_instruction.function_name]
            self.emit(('call', func_id))
            self.emit(('set_local', self.get_value(ir_instruction)))
        elif isinstance(ir_instruction, ir.Jump):
            block = ir_instruction.block
            self.fill_phis(block, ir_instruction.target)
            self.jump_block(ir_instruction.target)
        elif isinstance(ir_instruction, ir.CJump):
            self.emit(('get_local', self.get_value(ir_instruction.a)))
            self.emit(('get_local', self.get_value(ir_instruction.b)))
            cmp_ops = {
                '>': 'i32.gt_s'
            }
            op = cmp_ops[ir_instruction.cond]
            self.emit((op,))
            block = ir_instruction.block
            self.emit(('if', 'emptyblock'))
            self.fill_phis(block, ir_instruction.lab_yes)
            self.jump_block(ir_instruction.lab_yes)
            self.emit(('else', ))
            self.fill_phis(block, ir_instruction.lab_no)
            self.jump_block(ir_instruction.lab_no)
            self.emit(('end', ))
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

    def jump_block(self, b):
        nr = self.block_nrs[b]
        self.emit(('i32.const', nr))
        self.emit(('set_local', self.block_idx_var))

    def get_ty(self, ir_ty):
        """ Get the right wasm type for an ir type """
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
        """ Emit a single wasm instruction """
        instruction = components.Instruction(*instruction)
        print(instruction.to_text())  # instruction.to_bytes())
        self.instructions.append(instruction)
