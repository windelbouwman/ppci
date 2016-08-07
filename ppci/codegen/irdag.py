"""
    The process of instruction selection is preceeded by the creation of
    a selection dag (directed acyclic graph). The dagger take ir-code as
    input and produces such a dag for instruction selection.

    A DAG represents the logic (computation) of a single basic block.
"""

import logging
import re
from .. import ir
from ..arch.registers import Register
from ..arch.arch import Label
from ..binutils.debuginfo import FpOffsetAddress
from ..utils.tree import Tree
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


class FunctionInfo:
    """ Keeps track of global function data when generating code for part
    of a functions. """
    def __init__(self, frame):
        self.frame = frame
        self.value_map = {}  # mapping from ir-value to dag node
        self.label_map = {}
        self.epilog_label = None
        self.phi_map = {}  # mapping from phi node to vreg
        self.block_trees = {}  # Mapping from block to tree serie for block
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
        self.postfix_map = {
            ir.i64: 'I64', ir.i32: "I32", ir.i16: "I16", ir.i8: 'I8',
            ir.f32: 'F32', ir.f64: 'F64'}
        self.postfix_map[ir.ptr] = 'I{}'.format(arch.byte_sizes['ptr'] * 8)

    def build(self, ir_function, function_info):
        """ Create a selection graph for the given function.
            Selection graph is divided into groups for each basic block.
        """
        self.sgraph = SelectionGraph()
        self.function_info = function_info

        # TODO: fix this total mess with vreg, block and chains:
        self.current_block = None

        # Create maps for global variables:
        for variable in ir_function.module.variables:
            val = self.new_node('LABEL', value=make_label_name(variable))
            self.add_map(variable, val.new_output(variable.name))

        # Create start node:
        self.current_token = self.new_node('ENTRY').new_output(
            'token', kind=SGValue.CONTROL)

        # Generate nodes for all blocks:
        for ir_block in depth_first_order(ir_function):
            self.block_to_sgraph(ir_block, function_info)

        self.sgraph.check()
        return self.sgraph

    def block_to_sgraph(self, ir_block: ir.Block, function_info):
        """
            Create dag (directed acyclic graph) from a basic block.
            The resulting dag can be used for instruction selection.
        """
        assert isinstance(ir_block, ir.Block)

        self.current_block = ir_block

        # Create start node:
        entry_node = self.new_node('ENTRY')
        entry_node.value = ir_block
        self.current_token = entry_node.new_output(
            'token', kind=SGValue.CONTROL)

        # Emit extra dag for parameters when entry block:
        if ir_block.is_entry:
            self.entry_block_special_case(function_info, ir_block.function)

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
        sgnode = self.new_node('EXIT')
        sgnode.add_input(self.current_token)

    def do_jump(self, node):
        sgnode = self.new_node('JMP')
        sgnode.value = self.function_info.label_map[node.target]
        self.debug_db.map(node, sgnode)
        self.chain(sgnode)

    def make_opcode(self, opcode, typ):
        """ Generate typed opcode from opcode and type """
        return opcode + self.postfix_map[typ]

    def chain(self, sgnode):
        if self.current_token is not None:
            sgnode.add_input(self.current_token)
        self.current_token = sgnode.new_output('ctrl', kind=SGValue.CONTROL)

    def new_node(self, name, *args, value=None):
        """ Create a new selection graph node, and add it to the graph """
        sgnode = SGNode(name)
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
        vreg = self.function_info.frame.rv
        opcode = self.make_opcode('MOV', node.result.ty)
        mov_node = self.new_node(opcode, res, value=vreg)
        self.chain(mov_node)

        # Jump to epilog:
        sgnode = self.new_node('JMP')
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_c_jump(self, node):
        """ Process conditional jump into dag """
        lhs = self.get_value(node.a)
        rhs = self.get_value(node.b)
        cond = node.cond
        sgnode = self.new_node('CJMP', lhs, rhs)
        sgnode.value = cond, self.function_info.label_map[node.lab_yes],\
            self.function_info.label_map[node.lab_no]
        self.chain(sgnode)
        self.debug_db.map(node, sgnode)

    def do_exit(self, node):
        # Jump to epilog:
        sgnode = self.new_node('JMP')
        sgnode.value = self.function_info.epilog_label
        self.chain(sgnode)

    def do_alloc(self, node):
        """ Process the alloc instruction """
        # TODO: check alignment?
        fp = self.new_node(self.make_opcode("REG", ir.ptr), value=self.arch.fp)
        fp_output = fp.new_output('fp')
        fp_output.wants_vreg = False
        offset = self.new_node(self.make_opcode("CONST", ir.ptr))
        offset.value = self.function_info.frame.alloc(node.amount)
        offset_output = offset.new_output('offset')
        offset_output.wants_vreg = False
        sgnode = self.new_node(
            self.make_opcode('ADD', ir.ptr), fp_output, offset_output)
        # self.chain(sgnode)
        output = sgnode.new_output('alloc')
        output.wants_vreg = False
        self.add_map(node, output)
        if self.debug_db.contains(node):
            dbg_var = self.debug_db.get(node)
            dbg_var.address = FpOffsetAddress(offset.value)
        # self.debug_db.map(node, sgnode)

    def get_address(self, ir_address):
        """ Determine address for load or store. """
        if isinstance(ir_address, ir.Variable):
            # A global variable may be contained in another module
            # That is why it is created here, and not in the prepare step
            sgnode = self.new_node('LABEL', value=make_label_name(ir_address))
            address = sgnode.new_output('address')
        else:
            address = self.get_value(ir_address)
        return address

    def do_load(self, node):
        """ Create dag node for load operation """
        address = self.get_address(node.address)
        sgnode = self.new_node(self.make_opcode('LDR', node.ty), address)
        # Make sure a data dependence is added to this node
        self.debug_db.map(node, sgnode)
        self.chain(sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_store(self, node):
        """ Create a DAG node for the store operation """
        address = self.get_address(node.address)
        value = self.get_value(node.value)
        opcode = self.make_opcode('STR', node.value.ty)
        sgnode = self.new_node(opcode, address, value)
        self.chain(sgnode)
        self.debug_db.map(node, sgnode)

    def do_const(self, node):
        """ Process constant instruction """
        if isinstance(node.value, (int, float)):
            name = self.make_opcode('CONST', node.ty)
            value = node.value
        else:  # pragma: no cover
            raise NotImplementedError(str(type(node.value)))
        sgnode = self.new_node(name)
        self.debug_db.map(node, sgnode)
        sgnode.value = value
        output = sgnode.new_output(node.name)
        output.wants_vreg = False
        self.add_map(node, output)

    def do_literal_data(self, node):
        """ Literal data is stored after a label """
        label = self.function_info.frame.add_constant(node.data)
        sgnode = self.new_node('LABEL', value=label)
        self.add_map(node, sgnode.new_output(node.name))

    def do_binop(self, node):
        """ Visit a binary operator and create a DAG node """
        names = {'+': 'ADD', '-': 'SUB', '|': 'OR', '<<': 'SHL',
                 '*': 'MUL', '&': 'AND', '>>': 'SHR', '/': 'DIV',
                 '%': 'REM', '^': 'XOR'}
        op = self.make_opcode(names[node.operation], node.ty)
        a = self.get_value(node.a)
        b = self.get_value(node.b)
        sgnode = self.new_node(op, a, b)
        self.debug_db.map(node, sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    def do_cast(self, node):
        """ Create a cast of type """
        op = '{}TO{}'.format(
            self.postfix_map[node.src.ty], self.postfix_map[node.ty])
        a = self.get_value(node.src)
        sgnode = self.new_node(op, a)
        self.add_map(node, sgnode.new_output(node.name))

    def do_procedure_call(self, node):
        # This is the moment to move all parameters to new temp registers.
        args = []
        inputs = []
        for argument in node.arguments:
            arg_val = self.get_value(argument)
            loc = self.new_vreg(argument.ty)
            args.append(loc)
            opcode = self.make_opcode('MOV', argument.ty)
            arg_sgnode = self.new_node(opcode, arg_val, value=loc)
            self.chain(arg_sgnode)
            # inputs.append(arg_sgnode.new_output('x'))

        arg_types = [argument.ty for argument in node.arguments]
        # Perform the actual call:
        sgnode = self.new_node(
            'CALL',
            value=(node.function_name, arg_types, args))
        self.debug_db.map(node, sgnode)
        for i in inputs:
            sgnode.add_input(i)
        self.chain(sgnode)

    def do_function_call(self, node):
        # This is the moment to move all parameters to new temp registers.
        args = []
        inputs = []
        for argument in node.arguments:
            arg_val = self.get_value(argument)
            loc = self.new_vreg(argument.ty)
            args.append(loc)
            opcode = self.make_opcode('MOV', argument.ty)
            arg_sgnode = self.new_node(opcode, arg_val, value=loc)
            self.chain(arg_sgnode)
            # inputs.append(arg_sgnode.new_output('x'))

        # New register for copy of result:
        ret_val = self.function_info.frame.new_reg(
            self.arch.value_classes[node.ty], '{}_result'.format(node.name))

        arg_types = [argument.ty for argument in node.arguments]
        # Perform the actual call:
        sgnode = self.new_node(
            'CALL',
            value=(node.function_name, arg_types, node.ty, args, ret_val))
        self.debug_db.map(node, sgnode)
        for i in inputs:
            sgnode.add_input(i)
        self.chain(sgnode)

        # When using the call as an expression, use copy of return value:
        output = sgnode.new_output('res')
        output.vreg = ret_val
        self.add_map(node, output)

    def do_phi(self, node):
        """ Refer to the correct copy of the phi node """
        vreg = self.function_info.phi_map[node]
        sgnode = self.new_node(self.make_opcode('REG', node.ty), value=vreg)
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
                opcode = self.make_opcode('MOV', phi.ty)
                sgnode = self.new_node(opcode, val, value=vreg1)
                self.chain(sgnode)
                val_map[from_val] = vreg1

        # Step 2: copy the temporary value to the phi register:
        for succ_block in ir_block.successors:
            for phi in succ_block.phis:
                vreg = self.function_info.phi_map[phi]
                from_val = phi.get_value(ir_block)
                vreg1 = val_map[from_val]

                # Create reg node:
                sgnode1 = self.new_node(
                    self.make_opcode('REG', phi.ty), value=vreg1)
                val = sgnode1.new_output(vreg1.name)

                # Create move node:
                opcode = self.make_opcode('MOV', phi.ty)
                sgnode = self.new_node(opcode, val, value=vreg)
                self.chain(sgnode)

    def entry_block_special_case(self, function_info, ir_function):
        """ Copy arguments into new temporary registers """
        # TODO: maybe this can be done different
        # Copy parameters into fresh temporaries:
        for arg in ir_function.arguments:
            loc = function_info.frame.arg_locs[arg.num]
            # TODO: byte value are not always passed in byte registers..
            #
            tp_pf = 'REGI{}'.format(loc.bitsize)
            param_node = self.new_node(
                tp_pf,
                value=loc)
            assert isinstance(loc, Register)
            output = param_node.new_output(arg.name)
            vreg = function_info.frame.new_reg(
                self.arch.value_classes[arg.ty], twain=arg.name)
            output.vreg = vreg
            self.chain(param_node)

            # When refering the paramater, use the copied value:
            self.add_map(arg, output)


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


def topological_sort_modified(nodes, start):
    """ Modified topological sort, start at the end and work back """
    unmarked = set(nodes)
    marked = set()
    temp_marked = set()
    L = []

    def visit(n):
        if n not in nodes:
            return
        assert n not in temp_marked, 'DAG has cycles'
        if n in unmarked:
            temp_marked.add(n)

            # 1 satisfy control dependencies:
            for inp in n.control_inputs:
                visit(inp.node)

            # 2 memory dependencies:
            for inp in n.memory_inputs:
                visit(inp.node)

            # 3 data dependencies:
            for inp in n.data_inputs:
                visit(inp.node)
            temp_marked.remove(n)
            marked.add(n)
            unmarked.remove(n)
            L.append(n)

    # Start to visit with pre-knowledge of the last node!
    visit(start)
    while unmarked:
        node = next(iter(unmarked))
        visit(node)

    # Hack: move tail again to tail:
    if L:
        if L[-1] is not start:
            L.remove(start)
            L.append(start)
    return L


def make_op(op, vreg):
    typ = 'I{}'.format(vreg.bitsize)
    return '{}{}'.format(op, typ)


class DagSplitter:
    """ Class that splits a DAG into a series of trees. This series is sorted
        such that data dependencies are met. The trees can henceforth be
        used to match trees.
    """
    logger = logging.getLogger('dag-splitter')

    def __init__(self, arch, debug_db):
        self.arch = arch
        self.debug_db = debug_db

    def split_into_trees(self, sgraph, ir_function, function_info):
        """ Split a forest of trees into a sorted series of trees for each
            block.
        """
        self.assign_vregs(sgraph, function_info)
        for ir_block in ir_function:
            nodes = sgraph.get_group(ir_block)
            # Get rid of ENTRY and EXIT:
            nodes = set(
                filter(
                    lambda x: x.name not in ['ENTRY', 'EXIT'], nodes))

            tail_node = function_info.block_tails[ir_block]
            trees = self.make_trees(nodes, tail_node)
            function_info.block_trees[ir_block] = trees

    def assign_vregs(self, sgraph, function_info):
        """ Give vreg values to values that cross block boundaries """
        frame = function_info.frame
        for node in sgraph:
            if node.group:
                self.check_vreg(node, frame)

    def check_vreg(self, node, frame):
        """ Determine whether node outputs need a virtual register """
        assert node.group is not None

        for data_output in node.data_outputs:
            if (len(data_output.users) > 1) or node.volatile or \
                    any(u.group is not node.group
                        for u in data_output.users):
                if data_output.wants_vreg and not data_output.vreg:
                    cls = self.get_reg_class(data_output)
                    vreg = frame.new_reg(cls, data_output.name)
                    data_output.vreg = vreg

    def make_trees(self, nodes, tail_node):
        """ Create a tree from a list of sorted nodes. """
        sorted_nodes = topological_sort_modified(nodes, tail_node)
        trees = []
        node_map = {}

        def mk_tr(inp):
            if inp.vreg:
                # If the input value has a vreg, use it
                child_tree = Tree(make_op('REG', inp.vreg), value=inp.vreg)
            elif inp.node in node_map:
                child_tree = node_map[inp.node]
            elif inp.node.name == 'LABEL':
                child_tree = Tree(inp.node.name, value=inp.node.value)
            else:  # inp.node.name.startswith('CONST'):
                # If the node is a constant, use that
                assert not inp.wants_vreg
                children = [mk_tr(i) for i in inp.node.inputs]
                child_tree = Tree(
                    inp.node.name, *children, value=inp.node.value)
            return child_tree

        for node in sorted_nodes:
            assert len(node.data_outputs) <= 1

            # Determine data dependencies:
            children = []
            for inp in node.data_inputs:
                child_tree = mk_tr(inp)
                children.append(child_tree)

            # Create a tree node:
            tree = Tree(node.name, *children, value=node.value)
            self.debug_db.map(node, tree)

            # Handle outputs:
            if len(node.data_outputs) == 0:
                # If the tree was volatile, it must be emitted
                if node.volatile:
                    trees.append(tree)
            else:
                # If the output has a vreg, put the value in:
                data_output = node.data_outputs[0]
                if data_output.vreg:
                    vreg = data_output.vreg
                    tree = Tree(make_op('MOV', vreg), tree, value=vreg)
                    trees.append(tree)
                    tree = Tree(make_op('REG', vreg), value=vreg)
                elif node.volatile:
                    trees.append(tree)

            # Store for later:
            node_map[node] = tree
        return trees

    def get_reg_class(self, data_flow):
        """ Determine the register class suited for this data flow line """
        op = data_flow.node.name
        if op == 'LABEL':
            return self.arch.get_reg_class(ty=ir.ptr)
        assert 'I' in op
        bitsize = int(re.search('I(\d+)', op).group(1))
        return self.arch.get_reg_class(bitsize=bitsize)
