import logging
from ... import ir, relooper
from . import components


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
    logger = logging.getLogger('ir2wasm')

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

        # Store incoming arguments:
        # Locals are located in local 0, 1, 2 etc..
        for argument in ir_function.arguments:
            # Arguments are implicit locals
            self.get_value(argument)
        #    self.emit(('set_local', self.get_value(argument)))

        # Generate function code:
        # Transform ir-code in shaped code:
        self._block_stack = []
        shape, self.rmap = relooper.find_structure(ir_function)
        self.do_shape(shape)

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

    def _deprecated_fallback_codegen(self, ir_blocks):
        # This is emergency code, when we have code with a lot of goto's
        # we cannot determine the form of the code..

        # This code is kept here as a start for C-code which contains
        # unstructured goto statements.

        self.block_nrs = {}

        # Loop
        self.block_idx_var = self.get_value(ir.Const(1, 'labelidx', ir.i32))
        self.emit(('i32.const', 0))
        self.emit(('set_local', self.block_idx_var))

        # Emulated block jumps!
        self.emit(('block', 'emptyblock'))  # Outer block, breaks to end
        self.emit(('loop', 'emptyblock'))  # Loop block, breaks to here.

        depth = 0
        for ir_block in ir_blocks:
            self.emit(('block', 'emptyblock'))
            self.block_nrs[ir_block] = depth
            depth += 1

        # branch to the proper block by br_table-ing to the right exit
        self.emit(('block', 'emptyblock'))
        self.emit(('get_local', self.block_idx_var))
        self.emit(('br_table', *list(range(depth)), 0))
        self.emit(('end',))

        for ir_block in ir_blocks:
            self.do_block(ir_block)
            self.emit(('br', depth))  # Branch to loop
            depth -= 1
            self.emit(('end',))

        self.emit(('end',))
        self.emit(('end',))

    def do_shape(self, shape):
        """ Generate code for a given code shape """
        if isinstance(shape, relooper.BasicShape):
            ir_block = self.rmap[shape.content]
            # self.follow_blocks.append(follow)
            self.do_block(ir_block)
            # self.follow_blocks.pop(-1)
        elif isinstance(shape, relooper.SequenceShape):
            for sub_shape in shape.shapes:
                self.do_shape(sub_shape)
        elif isinstance(shape, relooper.IfShape):
            ir_block = self.rmap[shape.content]
            self.do_block(ir_block)
            self.push_block('if')
            self.emit(('if', 'emptyblock'))
            self.do_shape(shape.yes_shape)
            self.emit(('else', ))
            self.do_shape(shape.no_shape)
            self.emit(('end', ))
            self.pop_block('if')
        elif isinstance(shape, relooper.BreakShape):
            # Break out of the current loop!
            assert shape.level == 0
            self.emit(('br', self._get_block_level() + 1))
        elif isinstance(shape, relooper.ContinueShape):
            # Continue the current loop!
            assert shape.level == 0
            self.emit(('br', self._get_block_level()))
        elif isinstance(shape, relooper.LoopShape):
            self.push_block('loop')
            self.emit(('block', 'emptyblock'))  # Outer block, breaks to end
            self.emit(('loop', 'emptyblock'))  # Loop block, breaks to here.
            self.do_shape(shape.body)
            self.emit(('end',))
            self.emit(('end',))
            self.pop_block('loop')
        else:
            raise NotImplementedError(str(shape))

    def do_block(self, block):
        """ Generate code for the given block """
        self.logger.debug('Generating %s', block)
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
            self.fill_phis(ir_instruction)
            # Actual jump handled by shapes!
            # self.jump_block(ir_instruction.target)
        elif isinstance(ir_instruction, ir.CJump):
            self.emit(('get_local', self.get_value(ir_instruction.a)))
            self.emit(('get_local', self.get_value(ir_instruction.b)))
            cmp_ops = {
                '>': 'i32.gt_s',
                '>=': 'i32.ge_s',
                '<': 'i32.lt_s',
                '<=': 'i32.le_s',
                '==': 'i32.eq_s',
            }
            op = cmp_ops[ir_instruction.cond]
            self.emit((op,))
            # Fill all phis:
            self.fill_phis(ir_instruction)
            # Jump is handled by shapes!
        elif isinstance(ir_instruction, ir.Phi):
            # Phi nodes are handled in jumps to this block!
            pass
        else:
            raise NotImplementedError(str(ir_instruction))

    def fill_phis(self, ins):
        from_block = ins.block
        for to_block in from_block.successors:
            for i in to_block:
                if isinstance(i, ir.Phi):
                    v = i.get_value(from_block)
                    self.emit(('get_local', self.get_value(v)))
                    self.emit(('set_local', self.get_value(i)))

    def jump_block(self, b):
        # Lookup branch depth
        depth = self._block_stack.index(b)
        self.emit(('br', depth))  # Branch to loop

        # If all else fails, use backup plan:
        if False:
            raise NotImplementedError()
            # nr = self.block_nrs[b]
            # self.emit(('i32.const', nr))
            # self.emit(('set_local', self.block_idx_var))

    def get_ty(self, ir_ty):
        """ Get the right wasm type for an ir type """
        ty_map = {
            ir.i8: 'i32',
            ir.i16: 'i32',
            ir.i32: 'i32',
            ir.i64: 'i64',
            ir.f64: 'f64',
            ir.ptr: 'i32',  # TODO: for now assume we use 32 bit pointers.
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

    def push_block(self, kind):
        self._block_stack.append(kind)

    def pop_block(self, kind):
        assert self._block_stack.pop(-1) == kind

    def _get_block_level(self):
        """ Retrieve current block level for nearest break or continue """
        for i, kind in enumerate(reversed(self._block_stack)):
            if kind in ('loop',):
                return i
