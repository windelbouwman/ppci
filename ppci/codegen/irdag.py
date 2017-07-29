""" IR to DAG

The process of instruction selection is preceeded by the creation of
a selection DAG (directed acyclic graph). The dagger take ir-code as
input and produces such a dag for instruction selection.

A DAG represents the logic (computation) of a single basic block.

To do selection with tree matching, the DAG is then splitted into a
series of tree patterns. This is often referred to as a forest of trees.

.. autoclass:: ppci.codegen.irdag.SelectionGraphBuilder
    :members: build

"""

import logging
from .. import ir
from ..arch.generic_instructions import Label
from ..arch.stack import StackLocation
from ..arch.registers import Register
from ..binutils.debuginfo import FpOffsetAddress
from .selectiongraph import SGNode, SGValue, SelectionGraph


def prepare_function_info(arch, function_info, ir_function):
    """ Fill function info with labels for all basic blocks """
    # First define labels and phis:

    function_info.epilog_label = Label(
        make_label_name(ir_function) + '_epilog')

    for ir_block in ir_function:
        # Put label into map:
        function_info.label_map[ir_block] = Label(make_label_name(ir_block))

        # Create virtual registers for phi-nodes:
        for phi in ir_block.phis:
            vreg = function_info.frame.new_reg(
                arch.get_reg_class(ty=phi.ty), twain=phi.name)
            function_info.phi_map[phi] = vreg

    function_info.arg_vregs = []
    for arg in ir_function.arguments:
        # New vreg:
        vreg = function_info.frame.new_reg(
            arch.value_classes[arg.ty], twain=arg.name)
        function_info.arg_vregs.append(vreg)

    if isinstance(ir_function, ir.Function):
        function_info.rv_vreg = function_info.frame.new_reg(
            arch.get_reg_class(ty=ir_function.return_ty), twain='retval')

    function_info.arg_types = [a.ty for a in ir_function.arguments]


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

    def __init__(self, arch, debug_db):
        self.arch = arch
        self.debug_db = debug_db
        self.size_map = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}
        self.ptr_ty = self.size_map[arch.byte_sizes['ptr'] * 8]

    def build(self, ir_function: ir.SubRoutine, function_info):
        """ Create a selection graph for the given function.

        Selection graph is divided into groups for each basic block.
        """
        self.sgraph = SelectionGraph()
        self.function_info = function_info

        # TODO: fix this total mess with vreg, block and chains:
        self.current_block = None

        # Create maps for global variables:
        for variable in ir_function.module.variables:
            val = self.new_node('LABEL', ir.ptr)
            val.value = make_label_name(variable)
            self.add_map(variable, val.new_output(variable.name))

        self.load_arguments(ir_function, function_info)

        # Generate nodes for all blocks:
        for ir_block in depth_first_order(ir_function):
            self.block_to_sgraph(ir_block, function_info)

        self.store_return_value(ir_function, function_info)

        self.sgraph.check()
        return self.sgraph

    def load_arguments(self, ir_function, function_info):
        # HACK to enter this into entry block:
        self.current_block = 'foo'

        # Create start node:
        entry = self.new_node('ENTRY', None)
        self.current_token = entry.new_output('token', kind=SGValue.CONTROL)

        # Determine argument properties:
        args = ir_function.arguments
        arg_types = [a.ty for a in args]
        arg_locs = self.arch.determine_arg_locations(arg_types)

        # Mark incoming registers live:
        live_in = [l for l in arg_locs if isinstance(l, Register)]
        mark_node = self.new_node('VENTER', None, value=live_in)
        self.chain(mark_node)

        # Copy arguments:
        # TODO: this is now hardcoded for x86:
        stack_offset = 16

        arg_vregs = function_info.arg_vregs
        for arg, arg_loc, vreg in zip(args, arg_locs, arg_vregs):
            # if isinstance(arg_loc, Register):
            # TODO: implement memory copy
            if isinstance(arg_loc, Register):
                if arg_loc.bitsize != vreg.bitsize:
                    # Argument is a register, but requires a cast
                    # Determine proper code for register argument:
                    ty = arg.ty
                    if ty is ir.ptr:
                        ty = self.ptr_ty
                    x = '{}{}'.format(str(ty).upper()[0], arg_loc.bitsize)

                    # Convert to proper size using casting:
                    assert arg_loc.bitsize > vreg.bitsize
                    fp_node1 = self.new_node(
                        'REG', ir.get_ty(x), value=arg_loc)
                    fp_output1 = fp_node1.new_output(arg.name)
                    fp_output1.vreg = arg_loc
                    self.chain(fp_node1)

                    # Create conversion node:
                    fp_node2 = self.new_node(
                        '{}TO'.format(x), arg.ty, fp_output1)
                    fp_output = fp_node2.new_output(arg.name)
                    self.chain(fp_node2)
                else:
                    fp_node = self.new_node('REG', arg.ty, value=arg_loc)
                    fp_output = fp_node.new_output(arg.name)
                    fp_output.vreg = arg_loc
                    self.chain(fp_node)
            elif isinstance(arg_loc, StackLocation):
                # Argument is passed on stack, load it!
                sgnode = self.new_node('FPREL', ir.ptr, value=stack_offset)
                # TODO: hard coded for x86:
                stack_offset += 8
                bp = sgnode.new_output(arg.name)

                # Load it:
                fp_node = self.new_node('LDR', arg.ty, bp)
                fp_output = fp_node.new_output(arg.name)
                self.chain(fp_node)

                # TODO: This is a good place to copy stack passed structs
            else:
                raise NotImplementedError()

            # Move into new temp register:
            mov_node = self.new_node('MOV', arg.ty, fp_output, value=vreg)
            self.chain(mov_node)

            # Create temporary registers for aruments:
            param_node = self.new_node('REG', arg.ty, value=vreg)
            output = param_node.new_output(arg.name)
            output.vreg = vreg
            self.chain(param_node)

            # When refering the paramater, use the copied value:
            self.add_map(arg, output)

        # Hack hack hack:
        function_info.block_tails['foo'] = self.current_token.node

        sgnode = self.new_node('EXIT', None)
        sgnode.add_input(self.current_token)

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

    def store_return_value(self, ir_function, function_info):
        self.current_block = 'bar'

        # Create start node:
        entry = self.new_node('ENTRY', None)
        self.current_token = entry.new_output('token', kind=SGValue.CONTROL)

        if isinstance(ir_function, ir.Function):
            # Determine return value location:
            ty = ir_function.return_ty
            rv = self.arch.determine_rv_location(ty)

            # Fetch register containing return value:
            vreg = function_info.rv_vreg
            rv_node = self.new_node('REG', ty, value=vreg)
            rv_output = rv_node.new_output('rv')
            rv_output.vreg = vreg

            # Move return value into register:
            mov_node = self.new_node('MOV', ty, rv_output, value=rv)
            self.chain(mov_node)
            live_out = [rv]
        else:
            live_out = []

        # Mark outgoing registers live:
        mark_node = self.new_node('VEXIT', None, value=live_out)
        self.chain(mark_node)

        # End current group:
        function_info.block_tails['bar'] = self.current_token.node

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
        return self.function_info.frame.new_reg(self.arch.value_classes[ty])

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
        mov_node = self.new_node('MOV', node.result.ty, res, value=vreg)
        self.chain(mov_node)

        # Jump to epilog:
        sgnode = self.new_node('JMP', None)
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_c_jump(self, node):
        """ Process conditional jump into dag """
        lhs = self.get_value(node.a)
        rhs = self.get_value(node.b)
        cond = node.cond
        sgnode = self.new_node('CJMP', None, lhs, rhs)
        sgnode.value = cond, self.function_info.label_map[node.lab_yes],\
            self.function_info.label_map[node.lab_no]
        self.chain(sgnode)
        self.debug_db.map(node, sgnode)

    def do_exit(self, node):
        # Jump to epilog:
        sgnode = self.new_node('JMP', None)
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_alloc(self, node):
        """ Process the alloc instruction """
        # TODO: check alignment?
        # fp = self.new_node("REG", ir.ptr, value=self.arch.fp)
        # fp_output = fp.new_output('fp')
        # fp_output.wants_vreg = False
        # offset = self.new_node("CONST", ir.ptr)
        offset = self.function_info.frame.alloc(node.amount)
        # offset_output = offset.new_output('offset')
        # offset_output.wants_vreg = False
        sgnode = self.new_node('FPREL', ir.ptr, value=offset)

        output = sgnode.new_output('alloc')
        output.wants_vreg = False
        self.add_map(node, output)
        if self.debug_db.contains(node):
            dbg_var = self.debug_db.get(node)
            dbg_var.address = FpOffsetAddress(offset)
        # self.debug_db.map(node, sgnode)

    def get_address(self, ir_address):
        """ Determine address for load or store. """
        if isinstance(ir_address, ir.Variable):
            # A global variable may be contained in another module
            # That is why it is created here, and not in the prepare step
            sgnode = self.new_node('LABEL', ir.ptr)
            sgnode.value = make_label_name(ir_address)
            address = sgnode.new_output('address')
        else:
            address = self.get_value(ir_address)
        return address

    def do_load(self, node):
        """ Create dag node for load operation """
        address = self.get_address(node.address)
        sgnode = self.new_node('LDR', node.ty, address)
        # Make sure a data dependence is added to this node
        self.debug_db.map(node, sgnode)
        self.chain(sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_store(self, node):
        """ Create a DAG node for the store operation """
        address = self.get_address(node.address)
        value = self.get_value(node.value)
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
        inputs = []
        regouts = []
        for argument in node.arguments:
            arg_val = self.get_value(argument)
            loc = self.new_vreg(argument.ty)
            args.append((argument.ty, loc))
            arg_sgnode = self.new_node('MOV', argument.ty, arg_val, value=loc)
            self.chain(arg_sgnode)
            # reg_out = arg_sgnode.new_output('arg')
            # reg_out.vreg = loc
            # regouts.append(reg_out)
            # inputs.append(arg_sgnode.new_output('x'))
        return args

    def _make_call(self, node, args, rv):
        # Perform the actual call:
        sgnode = self.new_node('CALL', None)
        sgnode.value = (node.function_name, args, rv)
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
            self.arch.value_classes[node.ty], '{}_result'.format(node.name))

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

                # Create reg node:
                sgnode1 = self.new_node('REG', phi.ty, value=vreg1)
                val = sgnode1.new_output(vreg1.name)

                # Create move node:
                sgnode = self.new_node('MOV', phi.ty, val, value=vreg)
                self.chain(sgnode)


def make_label_name(dut):
    """ Returns the assembly code label name for the given ir-object """
    if isinstance(dut, ir.Block):
        return make_label_name(dut.function) + '_block_' + dut.name
    elif isinstance(dut, (ir.SubRoutine, ir.Variable)):
        return make_label_name(dut.module) + '_' + dut.name
    elif isinstance(dut, ir.Module):
        return dut.name
    else:  # pragma: no cover
        raise NotImplementedError(str(dut) + str(type(dut)))
