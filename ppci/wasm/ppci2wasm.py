""" Compile IR-code into Web Assembly (WASM).

IR-code is in SSA-form consisting of a soup of blocks. This means basic
blocks connected by jumps. Wasm on the other hand requires a stack
machine and structured control flow.

The compilation strategy is hence as follows:
- Transform SSA form of a function into expression trees
- Extract the structured control flow per function
- Walk over structured control shapes
- For each shape, evaluate the expression trees in it.

"""

import logging
from collections import defaultdict
from .. import ir
from ..graph import relooper
from . import components
from ..codegen.irdag import SelectionGraphBuilder, prepare_function_info
from ..codegen.irdag import FunctionInfo
from ..codegen.dagsplit import DagSplitter
from ..binutils import debuginfo
from .arch import WasmArchitecture
from .arch import I32Register, I64Register, F32Register, F64Register

def ir_to_wasm(ir_module: ir.Module, reporter=None) -> components.Module:
    """ Compiles ir-code to a wasm module.

    Args:
        ir_module (ir.Module): The ir-module to compile
        reporter: optionally report compilation steps

    Returns:
        A wasm module.
    """
    ir_to_wasm_compiler = IrToWasmCompiler(reporter=reporter)
    ir_to_wasm_compiler.prepare_compilation()
    ir_to_wasm_compiler.compile(ir_module)
    return ir_to_wasm_compiler.create_wasm_module()


class IrToWasmCompiler:
    """ Translates ir-code into wasm """
    logger = logging.getLogger('ir2wasm')
    STACKSIZE = 1000  # Virtual stack size

    def __init__(self, reporter=None):
        self.reporter = reporter

    def prepare_compilation(self):
        self.type_refs = {}  # Track signatures for re-use
        self.definitions = defaultdict(list)
        self.initial_memory = []
        self.tables = []  # Tables with function pointers
        self.global_vars = []
        self.global_labels = {}
        self.global_memory = self.STACKSIZE  # fill up global memory on the go!
        self.function_refs = {}
        self.pointed_functions = []  # List of referenced funcs
        
        # Global variables:
        # Keep track of virtual stack pointer:
        self.add_definition(
            components.Global(0, 'i32', True, [
                components.Instruction('i32.const', self.STACKSIZE)
            ]))
        self.global_labels['global0'] = 0  # todo: is this correct?
        self.sp_ref = components.Ref('global', index=0)
    
    def add_definition(self, definition):
        # print(definition.to_string())
        self.logger.debug('Create %s', definition)
        space = definition.__name__
        self.definitions[space].append(definition)

    def gather_definitions(self):
        """ Take all definitions by section id order: """
        definitions = []
        for name in components.SECTION_IDS:
            for definition in self.definitions[name]:
                definitions.append(definition)
        # print(definitions)
        return definitions

    def compile(self, ir_module):
        """ Compile an ir-module into a wasm module """
        self.logger.debug('Generating wasm for %s', ir_module)

        # Check external thingies:
        for i, ir_external in enumerate(ir_module.externals):
            if isinstance(ir_external, ir.ExternalSubRoutine):
                if self.has_function(ir_external.name):
                    pass
                    #raise ValueError(
                    #    'Function {} already defined'.format(ir_external.name))
                else:
                    arg_types = tuple(ir_external.argument_types)
                    if isinstance(ir_external, ir.ExternalFunction):
                        ret_types = (ir_external.return_type,)
                    else:
                        ret_types = ()
                    type_ref = self.get_type_id(arg_types, ret_types)
                    import_id = '$' + ir_external.name  # i
                    func_ref = components.Ref('func', index=i, name=import_id)
                    self.function_refs[ir_external.name] = func_ref
                    self.add_definition(
                        components.Import('js', ir_external.name, 'func', func_ref, (type_ref, )))
            else:
                raise NotImplementedError(str(ir_external))

        # Global variables:
        for ir_variable in ir_module.variables:
            addr = self.global_memory
            self.global_labels[ir_variable.name] = addr
            if ir_variable.value:
                self.initial_memory.append(
                    (0, addr, ir_variable.value))
            self.global_memory += ir_variable.amount

        functions_to_do = []

        # Register function numbers (for mutual recursive functions):
        for idx, ir_function in enumerate(ir_module.functions, len(self.function_refs)):
            if self.has_function(ir_function.name):
                raise ValueError(
                    'Function {} already defined'.format(ir_function.name))
            else:
                # Determine function signature:
                arg_types = tuple(a.ty for a in ir_function.arguments)
                if isinstance(ir_function, ir.Function):
                    ret_types = (ir_function.return_ty,)
                else:
                    ret_types = ()

                type_ref = self.get_type_id(arg_types, ret_types)

                # init func object, locals and instructions are attached later
                wasm_func = components.Func(
                    '$' + ir_function.name, type_ref, [], [])
                functions_to_do.append((ir_function, wasm_func))

                # Export all functions for now
                # todo: only export subset?
                func_ref = components.Ref('func', index=idx, name='$' + ir_function.name)
                self.function_refs[ir_function.name] = func_ref
                self.add_definition(
                    components.Export(
                        ir_function.name, 'func', func_ref))

        # Functions:
        for ir_function, wasm_func in functions_to_do:
            self.do_function(ir_function, wasm_func)

    def create_wasm_module(self):
        """ Finalize the wasm module and return it """

        self.add_definition(
            components.Memory(0, 10, None))  # Start with 10 pages?
        for memid, addr, data in self.initial_memory:
            offset = [
                components.Instruction('i32.const', addr),
            ]
            self.add_definition(
                components.Data(components.Ref('memory', index=memid),
                                offset, data))

        if self.pointed_functions:
            indexes = self.pointed_functions
            self.add_definition(
                components.Table(0, 'anyfunc', len(indexes), None))
            table_ref = components.Ref('table', index=0)
            print(indexes)
            offset = [
                components.Instruction('i32.const', 0),
            ]
            self.add_definition(
                components.Elem(
                    table_ref, offset, indexes))

        module = components.Module()
        module.definitions = self.gather_definitions()
        if self.reporter:
            self.reporter.dump_raw_text(module.to_string())
        return module

    def get_type_id(self, arg_types, ret_types):
        """ Get wasm type id and create a signature if required. """
        # Get type signature
        arg_types = tuple(self.get_ty(t) for t in arg_types)
        ret_types = tuple(self.get_ty(t) for t in ret_types)
        # Add to module if not already present
        key = arg_types, ret_types
        if key not in self.type_refs:
            type_id = len(self.type_refs)
            type_ref = components.Ref('type', index=type_id)
            self.type_refs[key] = type_ref
            self.add_definition(
                components.Type(type_id, [(i, a) for i, a in enumerate(arg_types)], ret_types))
        # Query the id for this sig
        return self.type_refs[key]

    def has_function(self, function_name):
        """ Get whether we already created an imported or defined
        function with the given name.
        """
        return function_name in self.function_refs

    def do_function(self, ir_function, wasm_func):
        """ Generate WASM for a single function """
        function_name = ir_function.name
        self.instructions = []
        self.local_var_map = {}
        self.local_vars = []
        self.stack = 0
        self.logger.debug('Generating wasm for %s', ir_function)

        # Generate function code:
        # Create a selection graph, so that we have expression trees
        arch = WasmArchitecture()
        sdagb = SelectionGraphBuilder(arch)
        frame = arch.new_frame(function_name, None)
        self.fi = FunctionInfo(frame)
        prepare_function_info(arch, self.fi, ir_function)
        dbdb = debuginfo.DebugDb()
        self.sdag = sdagb.build(ir_function, self.fi, dbdb)
        self.ds = DagSplitter(arch)
        self.ds.assign_vregs(self.sdag, self.fi)
        self.ds.split_into_trees(
            self.sdag, ir_function, self.fi, dbdb)

        # Place used literals in global memory:
        for lab, cv in frame.constants:
            assert isinstance(cv, bytes)
            addr = self.global_memory
            self.global_labels[lab] = addr
            self.initial_memory.append((0, addr, cv))
            self.global_memory += len(cv)

        self.increment_stack_pointer()

        # Locals are located in local 0, 1, 2 etc..
        # The first x locals are the function arguments.
        for i, argument_vreg in enumerate(self.fi.arg_vregs):
            self.local_var_map[argument_vreg] = components.Ref('local', index=i)

        # Transform ir-code in shaped code:
        self._block_stack = []
        shape, self.rmap = relooper.find_structure(ir_function)
        self.do_shape(shape)

        self.decrement_stack_pointer()

        if isinstance(ir_function, ir.Function):
            # Insert dummy value at end of function:
            # TODO: this is ugly!
            if self.instructions[-1].opcode != 'return':
                ret_type = self.get_ty(ir_function.return_ty)
                self.emit((ret_type + '.const', 0))

        # Add locals and instructions to the wasm funcion object
        wasm_func.locals = [(None, x) for x in self.local_vars]
        wasm_func.instructions = self.instructions
        self.add_definition(wasm_func)

    def increment_stack_pointer(self):
        """ Allocate stack if needed """
        if self.fi.frame.stacksize > 0:
            self.emit(('get_global', self.sp_ref))
            self.emit(('i32.const', self.fi.frame.stacksize))
            self.emit(('i32.sub',))
            self.emit(('set_global', self.sp_ref))

    def decrement_stack_pointer(self):
        if self.fi.frame.stacksize > 0:
            self.emit(('get_global', self.sp_ref))
            self.emit(('i32.const', self.fi.frame.stacksize))
            self.emit(('i32.add',))
            self.emit(('set_global', self.sp_ref))

    def do_shape(self, shape):
        """ Generate code for a given code shape """
        if isinstance(shape, relooper.BasicShape):
            ir_block = self.rmap[shape.content]
            self.do_block(ir_block)
        elif isinstance(shape, relooper.SequenceShape):
            for sub_shape in shape.shapes:
                if sub_shape is not None:
                    self.do_shape(sub_shape)
        elif isinstance(shape, relooper.IfShape):
            ir_block = self.rmap[shape.content]
            self.do_block(ir_block)
            assert self.stack == 1, str(self.stack)
            self.stack -= 1
            self.push_block('if')
            self.emit(('if', 'emptyblock'))
            assert self.stack == 0, str(self.stack)
            if shape.yes_shape is not None:
                self.do_shape(shape.yes_shape)
            if shape.no_shape is not None:
                self.emit(('else', ))
                self.do_shape(shape.no_shape)
            self.emit(('end', ))
            assert self.stack == 0, str(self.stack)
            self.pop_block('if')
        elif isinstance(shape, relooper.BreakShape):
            # Break out of the current loop!
            assert shape.level == 0
            assert self.stack == 0, str(self.stack)
            label_ref = components.Ref('label', index=(self._get_block_level() + 1))
            self.emit(('br', label_ref))
        elif isinstance(shape, relooper.ContinueShape):
            # Continue the current loop!
            assert shape.level == 0
            assert self.stack == 0, str(self.stack)
            label_ref = components.Ref('label', index=(self._get_block_level()))
            self.emit(('br', label_ref))
        elif isinstance(shape, relooper.LoopShape):
            assert self.stack == 0, str(self.stack)
            self.push_block('loop')
            self.emit(('block', 'emptyblock'))  # Outer block, breaks to end
            self.emit(('loop', 'emptyblock'))  # Loop block, breaks to here.
            self.do_shape(shape.body)
            self.emit(('end',))
            self.emit(('end',))
            self.pop_block('loop')
            assert self.stack == 0, str(self.stack)
        else:
            raise NotImplementedError(str(shape))

    def do_block(self, ir_block):
        """ Generate code for the given block """
        self.logger.debug('Generating %s', ir_block)
        block_trees = self.ds.split_group_into_trees(
            self.sdag, self.fi, ir_block)
        for tree in block_trees:
            # print(tree)
            self.do_tree(tree)
            # if tree.name == 'CALL' and

    unops = {
        'NEGI32',
    }

    binop_map = {
        'ADDI32': 'i32.add',
        'SUBI32': 'i32.sub',
        'MULI32': 'i32.mul',
        'DIVI32': 'i32.div_s',
        'ANDI32': 'i32.and',
        'ORI32': 'i32.or',
        'XORI32': 'i32.xor',
        'SHRI32': 'i32.shr_u',
        'SHLI32': 'i32.shl',
        'ADDU32': 'i32.add',
        'SUBU32': 'i32.sub',
        'MULU32': 'i32.mul',
        'DIVU32': 'i32.div_u',
        'REMI32': 'i32.rem_s',
        'REMU32': 'i32.rem_u',
        'ADDI64': 'i64.add',
        'SUBI64': 'i64.sub',
        'MULI64': 'i64.mul',
        'MULF32': 'f32.mul',
        'ADDF32': 'f32.add',
        'SUBF32': 'f32.sub',
        'DIVF32': 'f32.div',
        'MULF64': 'f64.mul',
        'ADDF64': 'f64.add',
        'SUBF64': 'f64.sub',
        'DIVF64': 'f64.div',
    }

    cmp_ops = {
        '>': 'gt',
        '>=': 'ge',
        '<': 'lt',
        '<=': 'le',
        '==': 'eq',
        '!=': 'ne',
    }

    store_opcodes = {
        'STRI8': 'i32.store8',
        'STRU8': 'i32.store8',
        'STRI16': 'i32.store16',
        'STRU16': 'i32.store16',
        'STRI32': 'i32.store',
        'STRU32': 'i64.store32',  # TODO
        'STRI64': 'i64.store',
        'STRF32': 'f32.store',
        'STRF64': 'f64.store',
    }

    load_opcodes = {
        'LDRI8': 'i32.load8_s',
        'LDRU8': 'i32.load8_u',
        'LDRI16': 'i32.load16_s',
        'LDRU16': 'i32.load16_u',
        'LDRI32': 'i32.load',
        'LDRU32': 'i64.load32_u',
        'LDRI64': 'i64.load',
        'LDRF32': 'f32.load',
        'LDRF64': 'f64.load',
    }

    const_opcodes = {
        'CONSTI8': 'i32.const',
        'CONSTU8': 'i32.const',
        'CONSTI16': 'i32.const',
        'CONSTU16': 'i32.const',
        'CONSTI32': 'i32.const',
        'CONSTI64': 'i64.const',
        'CONSTU64': 'i64.const',
        'CONSTF32': 'f32.const',
        'CONSTF64': 'f64.const',
    }

    cast_operators = {
        'I32TOI32', 'I32TOU32', 'U32TOI32', 'U32TOU32',
        'I32TOI8', 'I8TOI32', 'I32TOU8', 'U8TOI32',
        'U32TOU8', 'U8TOU32',
        'I32TOI16', 'I16TOI32',
    }

    cast_operators2 = {
        'F32TOI32': ['f32.nearest', 'i32.trunc_s/f32'],
        'F32TOU32': ['f32.nearest', 'i32.trunc_u/f32'],
        'F32TOI64': ['f32.nearest', 'i64.trunc_s/f32'],
        'F32TOU64': ['f32.nearest', 'i64.trunc_u/f32'],
        'F64TOI64': ['f64.nearest', 'i64.trunc_s/f64'],
        'F64TOU64': ['f64.nearest', 'i64.trunc_u/f64'],
        'F64TOI32': ['f64.nearest', 'i32.trunc_s/f64'],
        'F64TOU32': ['f64.nearest', 'i32.trunc_u/f64'],
        'U64TOF64': ['f64.convert_u/i64'],
        'I64TOF64': ['f64.convert_s/i64'],
        'U32TOF64': ['f64.convert_u/i32'],
        'I32TOF64': ['f64.convert_s/i32'],
        'I32TOF32': ['f32.convert_s/i32'],
        'U32TOF32': ['f32.convert_u/i32'],
        'F64TOF32': ['f32.demote/f64'],
        'F32TOF64': ['f64.promote/f32'],
    }

    reg_operators = {
        'REGI8', 'REGU8',
        'REGI16', 'REGU16',
        'REGI32', 'REGU32',
        'REGI64', 'REGU32',
        'REGF32', 'REGF64',
    }

    mov_operators = {
        'MOVI8', 'MOVU8',
        'MOVI16', 'MOVU16',
        'MOVI32', 'MOVU32',
        'MOVI64', 'MOVU64',
        'MOVF32', 'MOVF64',
    }

    cmp_operators = {
        'CJMPI8': ir.i8, 'CJMPU8': ir.u8,
        'CJMPI16': ir.i16, 'CJMPU16': ir.u16,
        'CJMPI32': ir.i32, 'CJMPU32': ir.u32,
        'CJMPI64': ir.i64, 'CJMPU64': ir.u64,
        'CJMPF32': ir.f32, 'CJMPF64': ir.f64
    }

    def do_tree(self, tree):
        """ Implement proper logic for an ir instruction """
        # TODO: we might have used codegen.treeselector class here...
        if tree.name in self.binop_map:
            self.do_tree(tree[0])
            self.do_tree(tree[1])
            opcode = self.binop_map[tree.name]
            self.stack -= 1
            self.emit((opcode, ))
        elif tree.name in self.mov_operators:
            self.do_tree(tree[0])
            self.emit(('set_local', self.get_value(tree.value)))
            self.stack -= 1
        elif tree.name in self.reg_operators:
            self.emit(('get_local', self.get_value(tree.value)))
            self.stack += 1
        elif tree.name == 'NEGI32':
            self.emit(('i32.const', 0))
            self.do_tree(tree[0])
            self.emit(('i32.sub',))
        elif tree.name in ['FPRELI32']:
            addr = tree.value.offset
            self.emit(('get_global', self.sp_ref))  # Fetch stack pointer
            self.emit(('i32.const', addr))
            self.emit(('i32.add',))
            self.stack += 1
        elif tree.name in self.store_opcodes:
            self.do_tree(tree[0])
            self.do_tree(tree[1])
            store_op = self.store_opcodes[tree.name]
            self.emit((store_op, 0, 0))
            self.stack -= 2
        elif tree.name in self.load_opcodes:
            self.do_tree(tree[0])
            load_op = self.load_opcodes[tree.name]
            self.emit((load_op, 0, 0))  # offset, align
        elif tree.name in self.const_opcodes:
            opcode = self.const_opcodes[tree.name]
            self.emit((opcode, tree.value))
            self.stack += 1
        elif tree.name == 'LABEL':  # isinstance(tree, ir.LiteralData):
            if tree.value in self.global_labels:
                addr = self.global_labels[tree.value]
            elif self.has_function(tree.value):
                # Taking pointer of function
                func_ref = self.function_refs[tree.value]
                addr = len(self.pointed_functions)
                self.global_labels[tree.value] = addr
                self.pointed_functions.append(func_ref)
            else:  # pragma: no cover
                raise NotImplementedError()
            self.emit(('i32.const', addr))
            self.stack += 1
        elif tree.name in self.cast_operators:
            self.do_tree(tree[0])
        elif tree.name in self.cast_operators2:
            self.do_tree(tree[0])
            opcodes = self.cast_operators2[tree.name]
            for opcode in opcodes:
                self.emit((opcode, ))
        elif tree.name == 'CALL':
            function_name, argv, rv = tree.value
            for ty, argument in argv:
                self.emit(('get_local', self.get_value(argument)))

            if isinstance(function_name, str):
                func_ref = self.function_refs[function_name]
                self.emit(('call', func_ref))
            else:
                # Handle function pointers:
                self.emit(('get_local', self.get_value(function_name)))
                arg_types = tuple(t for t, a in argv)
                ret_types = (rv[0],) if rv else tuple()
                type_ref = self.get_type_id(arg_types, ret_types)
                table_ref = components.Ref('table', index=0)
                self.emit(('call_indirect', type_ref, table_ref))

            if rv:
                self.emit(('set_local', self.get_value(rv[1])))
        elif tree.name == 'JMP':
            # Actual jump handled by shapes!
            if tree.value is self.fi.epilog_label:
                self.decrement_stack_pointer()
                # We are returning from function!
                if hasattr(self.fi, 'rv_vreg') and self.fi.rv_vreg:
                    self.emit(('get_local', self.get_value(self.fi.rv_vreg)))
                self.emit(('return',))
        elif tree.name in self.cmp_operators:
            # Ensure operands are on stack:
            self.do_tree(tree[0])
            self.do_tree(tree[1])

            # Create the opcode
            op = tree.value[0]
            ir_ty = self.cmp_operators[tree.name]
            opcode = self.get_ty(ir_ty) + '.' + self.cmp_ops[op]
            if op in ['<', '<=', '>', '>=']:
                if ir_ty.is_signed:
                    opcode += '_s'
                if ir_ty.is_unsigned:
                    opcode += '_u'

            self.emit((opcode,))
            self.stack -= 1
            # Jump is handled by shapes!
        else:
            raise NotImplementedError(str(tree))

    def get_ty(self, ir_ty):
        """ Get the right wasm type for an ir type """
        ty_map = {
            ir.i8: 'i32', ir.u8: 'i32',
            ir.i16: 'i32', ir.u16: 'i32',
            ir.i32: 'i32',
            ir.u32: 'i64',  # TODO: Should u32 map to i64?
            ir.i64: 'i64', ir.u64: 'i64',
            ir.f64: 'f64', ir.f32: 'f32',
            ir.ptr: 'i32',  # TODO: for now assume we use 32 bit pointers.
        }
        return ty_map[ir_ty]

    def get_value(self, value):
        """ Create a local number for the given value """
        if value not in self.local_var_map:
            self.local_var_map[value] = components.Ref('local', index=len(self.local_var_map))
            ty_map = {
                I32Register: 'i32', I64Register: 'i64',
                F32Register: 'f32', F64Register: 'f64',
            }
            wasm_ty = ty_map[type(value)]
            self.local_vars.append(wasm_ty)
        return self.local_var_map[value]

    def emit(self, instruction):
        """ Emit a single wasm instruction """
        instruction = components.Instruction(*instruction)
        # print(instruction.to_string())  # , instruction.to_bytes())
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
