""" IR to DAG

The process of instruction selection is preceeded by the creation of
a selection DAG (directed acyclic graph). The dagger take ir-code as
input and produces such a dag for instruction selection.

A DAG represents the logic (computation) of a single basic block.

To do selection with tree matching, the DAG is then splitted into a
series of tree patterns. This is often referred to as a forest of trees.

"""

import itertools
import logging
from .. import ir
from ..arch.generic_instructions import Label
from ..arch.stack import StackLocation
from ..binutils.debuginfo import FpOffsetAddress
from .selectiongraph import SGNode, SGValue, SelectionGraph


def prepare_function_info(arch, function_info, ir_function):
    """ Fill function info with labels for all basic blocks """
    # First define labels and phis:

    function_info.epilog_label = Label(ir_function.name + '_epilog')

    for ir_block in ir_function:
        # Put label into map:
        function_info.label_map[ir_block] = Label(ir_block.name)

        # Create virtual registers for phi-nodes:
        for phi in ir_block.phis:
            vreg = function_info.frame.new_reg(
                arch.get_reg_class(ty=phi.ty), twain=phi.name)
            function_info.phi_map[phi] = vreg

    function_info.arg_vregs = []
    function_info.arg_types = [a.ty for a in ir_function.arguments]
    if hasattr(arch, 'determine_arg_locations'):
        arg_locs = arch.determine_arg_locations(function_info.arg_types)
    else:
        arg_locs = range(len(ir_function.arguments))

    for arg, phys_loc in zip(ir_function.arguments, arg_locs):
        if arg.ty in arch.info.value_classes:
            # New vreg:
            vreg = function_info.frame.new_reg(
                arch.info.value_classes[arg.ty], twain=arg.name)
        else:
            # Allocate space on stack for this argument:
            # vreg = function_info.frame.alloc(arg.ty.size, 1)
            # print(phys_loc)
            vreg = phys_loc
        function_info.arg_vregs.append(vreg)

    if isinstance(ir_function, ir.Function):
        if ir_function.return_ty in arch.info.value_classes:
            function_info.rv_vreg = function_info.frame.new_reg(
                arch.get_reg_class(ty=ir_function.return_ty), twain='retval')
        else:
            function_info.rv_vreg = None


class FunctionInfo:
    """ Keeps track of global function data when generating code for part
    of a functions. """
    def __init__(self, frame):
        self.frame = frame
        self.value_map = {}  # mapping from ir-value to dag node
        self.label_map = {}
        self.epilog_label = None
        self.phi_map = {}  # mapping from phi node to vreg
        self.block_tails = {}


def depth_first_order(function):
    """ Return blocks in depth first search order """
    blocks = [function.entry]
    L = [function.entry]
    while L:
        b = L.pop(0)
        for b2 in b.successors:
            if b2 not in blocks:
                blocks.append(b2)
                L.append(b2)
    return blocks


class Operation:
    """ A single operation with a type """
    def __init__(self, op, ty):
        self.op = op
        self.ty = ty
        # assert ty, str(op)+str(ty)
        if op == 'MOV' and ty is None:
            raise AssertionError('MOV must not have type none')

    def __str__(self):
        if self.ty is None or self.op in ['LABEL', 'CALL']:
            return self.op.upper()
        else:
            return '{}{}'.format(self.op, str(self.ty)).upper()


def make_map(cls):
    """
        Add an attribute to the class that is a map of ir types to handler
        functions. For example if a function is called do_phi it will be
        registered into f_map under key ir.Phi.
    """
    f_map = getattr(cls, 'f_map')
    for name, func in list(cls.__dict__.items()):
        if name.startswith('do_'):
            tp_name = ''.join(x.capitalize() for x in name[2:].split('_'))
            ir_class = getattr(ir, tp_name)
            f_map[ir_class] = func
    return cls


@make_map
class SelectionGraphBuilder:
    """ Create a selectiongraph from a function for instruction selection """
    logger = logging.getLogger('selection-graph-builder')
    f_map = {}

    def __init__(self, arch):
        self.arch = arch
        # size_map = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}
        self.ptr_ty = arch.info.type_infos['ptr']

    def build(self, ir_function: ir.SubRoutine, function_info, debug_db):
        """ Create a selection graph for the given function.

        Selection graph is divided into groups for each basic block.
        """
        self.debug_db = debug_db
        self.sgraph = SelectionGraph()
        self.function_info = function_info

        # TODO: fix this total mess with vreg, block and chains:
        self.current_block = None

        # Create maps for global variables:
        for variable in itertools.chain(
                ir_function.module.variables, ir_function.module.functions, ir_function.module.externals):
            val = self.new_node('LABEL', ir.ptr)
            val.value = variable.name
            self.add_map(variable, val.new_output(variable.name))

        self.current_token = self.new_node('ENTRY', None).new_output(
            'token', kind=SGValue.CONTROL)

        # Create temporary registers for aruments:
        for arg, vreg in zip(ir_function.arguments, function_info.arg_vregs):
            if isinstance(vreg, StackLocation):
                param_node = self.new_node('FPREL', ir.ptr, value=vreg)
                output = param_node.new_output(arg.name)
                output.wants_vreg = False
            else:
                param_node = self.new_node('REG', arg.ty, value=vreg)
                output = param_node.new_output(arg.name)
                output.vreg = vreg

            # When refering the paramater, use the copied value:
            self.add_map(arg, output)

            self.chain(param_node)

        # Generate nodes for all blocks:
        for ir_block in depth_first_order(ir_function):
            self.block_to_sgraph(ir_block, function_info)

        self.sgraph.check()
        return self.sgraph

    def block_to_sgraph(self, ir_block: ir.Block, function_info):
        """ Create dag (directed acyclic graph) from a basic block.

        The resulting dag can be used for instruction selection.
        """
        assert isinstance(ir_block, ir.Block)

        self.current_block = ir_block

        # Create start node:
        entry_node = self.new_node('ENTRY', None)
        entry_node.value = ir_block
        self.current_token = entry_node.new_output(
            'token', kind=SGValue.CONTROL)

        # Generate series of trees:
        for instruction in ir_block:
            # In case of last statement, first perform phi-lifting:
            if instruction.is_terminator:
                self.copy_phis_of_successors(ir_block)

            # Dispatch the handler depending on type:
            self.f_map[type(instruction)](self, instruction)

        # Save tail node of this block:
        function_info.block_tails[ir_block] = self.current_token.node

        # Create end node:
        sgnode = self.new_node('EXIT', None)
        sgnode.add_input(self.current_token)

    def do_jump(self, node):
        sgnode = self.new_node('JMP', None)
        sgnode.value = self.function_info.label_map[node.target]
        self.debug_db.map(node, sgnode)
        self.chain(sgnode)

    def chain(self, sgnode):
        if self.current_token is not None:
            sgnode.add_input(self.current_token)
        self.current_token = sgnode.new_output('ctrl', kind=SGValue.CONTROL)

    def new_node(self, name, ty, *args, value=None):
        """ Create a new selection graph node, and add it to the graph """
        assert isinstance(name, str)
        assert isinstance(ty, ir.Typ) or ty is None
        # assert isinstance(name, Operation)
        if ty is ir.ptr:
            ty = self.ptr_ty
        sgnode = SGNode(Operation(name, ty))
        sgnode.add_inputs(*args)
        sgnode.value = value
        sgnode.group = self.current_block
        self.sgraph.add_node(sgnode)
        return sgnode

    def new_vreg(self, ty):
        """ Generate a new temporary fitting for the given type """
        return self.function_info.frame.new_reg(
            self.arch.info.value_classes[ty])

    def add_map(self, node, sgvalue):
        assert isinstance(node, ir.Value)
        assert isinstance(sgvalue, SGValue)
        self.function_info.value_map[node] = sgvalue

    def get_value(self, node):
        return self.function_info.value_map[node]

    def do_return(self, node):
        """ Move result into result register and jump to epilog """
        res = self.get_value(node.result)
        vreg = self.function_info.rv_vreg
        if vreg:
            mov_node = self.new_node('MOV', node.result.ty, res, value=vreg)
            self.chain(mov_node)
        else:  # pragma: no cover
            raise NotImplementedError('Pass pointer as first arg instead')

        # Jump to epilog:
        sgnode = self.new_node('JMP', None)
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_c_jump(self, node):
        """ Process conditional jump into dag """
        lhs = self.get_value(node.a)
        rhs = self.get_value(node.b)
        assert node.a.ty is node.b.ty
        cond = node.cond
        sgnode = self.new_node('CJMP', node.a.ty, lhs, rhs)
        sgnode.value = cond, self.function_info.label_map[node.lab_yes],\
            self.function_info.label_map[node.lab_no]
        self.chain(sgnode)
        self.debug_db.map(node, sgnode)

    def do_exit(self, node):
        # Jump to epilog:
        sgnode = self.new_node('JMP', None)
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_address_of(self, node):
        """ Process ir.AddressOf instruction """
        address = self.get_value(node.src)
        self.add_map(node, address)
        return address

    def do_alloc(self, node):
        """ Process the alloc instruction """
        # TODO: check alignment?
        # fp = self.new_node("REG", ir.ptr, value=self.arch.fp)
        # fp_output = fp.new_output('fp')
        # fp_output.wants_vreg = False
        # offset = self.new_node("CONST", ir.ptr)
        slot = self.function_info.frame.alloc(node.amount, node.alignment)
        # offset_output = offset.new_output('offset')
        # offset_output.wants_vreg = False
        sgnode = self.new_node('FPREL', ir.ptr, value=slot)

        output = sgnode.new_output('alloc')
        output.wants_vreg = False
        self.add_map(node, output)
        if self.debug_db.contains(node):
            dbg_var = self.debug_db.get(node)
            dbg_var.address = FpOffsetAddress(slot)
        # self.debug_db.map(node, sgnode)

    def do_copy_blob(self, node):
        pass

    def get_address(self, ir_address):
        """ Determine address for load or store. """
        if isinstance(ir_address, ir.GlobalValue):
            # A global variable may be contained in another module
            # That is why it is created here, and not in the prepare step
            sgnode = self.new_node('LABEL', ir.ptr)
            sgnode.value = ir_address.name
            address = sgnode.new_output('address')
        else:
            address = self.get_value(ir_address)
        return address

    def do_load(self, node):
        """ Create dag node for load operation """
        address = self.get_address(node.address)
        if isinstance(node.ty, ir.BlobDataTyp):
            sgnode = self.new_node('MOVB', None, address)
        else:
            sgnode = self.new_node('LDR', node.ty, address)
        # Make sure a data dependence is added to this node
        self.debug_db.map(node, sgnode)
        self.chain(sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_store(self, node):
        """ Create a DAG node for the store operation """
        address = self.get_address(node.address)
        value = self.get_value(node.value)
        if node.value.ty.is_blob:
            size = node.value.ty.size
            sgnode = self.new_node('MOVB', None, address, value, value=size)
        else:
            sgnode = self.new_node('STR', node.value.ty, address, value)
        self.chain(sgnode)
        self.debug_db.map(node, sgnode)

    def do_const(self, node):
        """ Process constant instruction """
        if isinstance(node.value, (int, float)):
            value = node.value
        else:  # pragma: no cover
            raise NotImplementedError(str(type(node.value)))
        sgnode = self.new_node('CONST', node.ty)
        self.debug_db.map(node, sgnode)
        sgnode.value = value
        output = sgnode.new_output(node.name)
        output.wants_vreg = False
        self.add_map(node, output)

    def do_literal_data(self, node):
        """ Literal data is stored after a label """
        label = self.function_info.frame.add_constant(node.data)
        sgnode = self.new_node('LABEL', ir.ptr, value=label)
        self.add_map(node, sgnode.new_output(node.name))

    def do_unop(self, node):
        """ Visit an unary operator and create a DAG node """
        names = {'-': 'NEG', '~': 'INV'}
        op = names[node.operation]
        a = self.get_value(node.a)
        sgnode = self.new_node(op, node.ty, a)
        self.debug_db.map(node, sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_binop(self, node):
        """ Visit a binary operator and create a DAG node """
        names = {'+': 'ADD', '-': 'SUB', '|': 'OR', '<<': 'SHL',
                 '*': 'MUL', '&': 'AND', '>>': 'SHR', '/': 'DIV',
                 '%': 'REM', '^': 'XOR'}
        op = names[node.operation]
        a = self.get_value(node.a)
        b = self.get_value(node.b)
        sgnode = self.new_node(op, node.ty, a, b)
        self.debug_db.map(node, sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_cast(self, node):
        """ Create a cast of type """
        from_ty = node.src.ty
        if from_ty is ir.ptr:
            from_ty = self.ptr_ty
        op = '{}TO'.format(str(from_ty).upper())
        a = self.get_value(node.src)
        sgnode = self.new_node(op, node.ty, a)
        self.add_map(node, sgnode.new_output(node.name))

    def _prep_call_arguments(self, node):
        """ Prepare call arguments into proper locations """
        # This is the moment to move all parameters to new temp registers.
        args = []
        for argument in node.arguments:
            arg_val = self.get_value(argument)
            if argument.ty.is_blob:
                args.append((argument.ty, arg_val.node.value))
            else:
                loc = self.new_vreg(argument.ty)
                args.append((argument.ty, loc))
                arg_sgnode = self.new_node(
                    'MOV', argument.ty, arg_val, value=loc)
                self.chain(arg_sgnode)
            # reg_out = arg_sgnode.new_output('arg')
            # reg_out.vreg = loc
            # regouts.append(reg_out)
            # inputs.append(arg_sgnode.new_output('x'))
        return args

    def _make_call(self, node, args, rv):
        if isinstance(node.callee, (ir.SubRoutine, ir.ExternalSubRoutine)):
            call_target = node.callee.name
        else:
            fptr = self.get_value(node.callee)

            fptr_vreg = self.new_vreg(ir.ptr)
            fptr_sgnode = self.new_node('MOV', ir.ptr, fptr, value=fptr_vreg)
            self.chain(fptr_sgnode)
            call_target = fptr_vreg

        # Perform the actual call:
        sgnode = self.new_node('CALL', None)
        sgnode.value = (call_target, args, rv)
        self.debug_db.map(node, sgnode)
        # for i in inputs:
        #    sgnode.add_input(i)
        self.chain(sgnode)

    def do_procedure_call(self, node):
        """ Transform a procedure call """
        args = self._prep_call_arguments(node)
        self._make_call(node, args, None)

    def do_function_call(self, node):
        """ Transform a function call """
        args = self._prep_call_arguments(node)

        # New register for copy of result:
        ret_val = self.function_info.frame.new_reg(
            self.arch.info.value_classes[node.ty],
            '{}_result'.format(node.name))

        rv = (node.ty, ret_val)
        self._make_call(node, args, rv)

        # When using the call as an expression, use the return value vreg:
        sgnode = self.new_node('REG', node.ty, value=ret_val)
        output = sgnode.new_output('res')
        output.vreg = ret_val
        self.add_map(node, output)

    def do_phi(self, node):
        """ Refer to the correct copy of the phi node """
        vreg = self.function_info.phi_map[node]
        sgnode = self.new_node('REG', node.ty, value=vreg)
        output = sgnode.new_output(node.name)
        output.vreg = vreg
        self.add_map(node, output)
        self.debug_db.map(node, vreg)

    def copy_phis_of_successors(self, ir_block):
        """ When a terminator instruction is encountered, handle the copy
        of phi values into the expected virtual register """
        # Copy values to phi nodes in other blocks:
        # step 1: create a new temporary that contains the value of the phi
        # node. Do this because the calculation of the value can involve the
        # phi vreg itself.
        val_map = {}
        for succ_block in ir_block.successors:
            for phi in succ_block.phis:
                from_val = phi.get_value(ir_block)
                val = self.get_value(from_val)
                vreg1 = self.new_vreg(phi.ty)
                sgnode = self.new_node('MOV', phi.ty, val, value=vreg1)
                self.chain(sgnode)
                val_map[from_val] = vreg1

        # Step 2: copy the temporary value to the phi register:
        for succ_block in ir_block.successors:
            for phi in succ_block.phis:
                vreg = self.function_info.phi_map[phi]
                from_val = phi.get_value(ir_block)
                vreg1 = val_map[from_val]

                # TODO: ensure this is valid:
                # In case phi input is phi itself, do not copy value:
                # if vreg is vreg1:
                #    continue

                # Create reg node:
                sgnode1 = self.new_node('REG', phi.ty, value=vreg1)
                val = sgnode1.new_output(vreg1.name)

                # Create move node:
                sgnode = self.new_node('MOV', phi.ty, val, value=vreg)
                self.chain(sgnode)
