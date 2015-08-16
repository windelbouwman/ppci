"""
    The process of instruction selection is preceeded by the creation of
    a selection dag (directed acyclic graph). The dagger take ir-code as
    input and produces such a dag for instruction selection.

    A DAG represents the logic (computation) of a single basic block.
"""

import logging
from .. import ir
from ..target.isa import Register
from ..target.target import Label
from .selectiongraph import SGNode, SGValue, SelectionGraph


NODE_ATTR = '$nodetype$$$'


def register(tp):
    """ Register a function for type tp """
    def reg_f(f):
        # f_map[tp] = f
        setattr(f, NODE_ATTR, tp)
        return f
    return reg_f


def make_map(cls):
    f_map = {}
    for name, func in list(cls.__dict__.items()):
        if hasattr(func, NODE_ATTR):
            tp = getattr(func, NODE_ATTR)
            f_map[tp] = func
    setattr(cls, 'f_map', f_map)
    return cls


def type_postfix(typ):
    """ Determine the name of the dag item """
    postfix_map = {ir.i32: "I32", ir.i16: "I16", ir.ptr: "I32", ir.i8: 'I8'}
    return postfix_map[typ]


def make_opcode(opcode, typ):
    """ Generate typed opcode from opcode and type """
    return opcode + type_postfix(typ)


def prepare_function_info(function_info, ir_function):
    """ Fill function info with labels for all basic blocks """
    # First define labels and phis:
    for ir_block in ir_function:
        # Put label into map:
        function_info.label_map[ir_block] = Label(ir.label_name(ir_block))

        # Create phi virtual registers:
        for phi in ir_block.phis:
            vreg = function_info.frame.new_virtual_register(
                twain=phi.name)
            function_info.phi_map[phi] = vreg


class FunctionInfo:
    """ Keeps track of global function data when generating code for part
    of a functions. """
    def __init__(self, frame):
        self.frame = frame
        self.value_map = {}  # mapping from ir-value to dag node
        self.label_map = {}
        self.phi_map = {}  # mapping from phi node to vreg
        self.block_roots = {}  # Mapping from block to root of block


@make_map
class SelectionGraphBuilder:
    def __init__(self):
        self.logger = logging.getLogger('selection-graph-builder')

    @register(ir.Jump)
    def do_jump(self, node):
        sgnode = self.new_node('JMP')
        sgnode.value = self.function_info.label_map[node.target]
        self.chain(sgnode)

    def chain(self, sgnode):
        if self.current_token is not None:
            sgnode.add_input(self.current_token)
        self.current_token = sgnode.new_output('ctrl', kind=SGValue.CONTROL)

    def mem_chain(self):
        pass

    def new_node(self, name, *args, value=None):
        """ Create a new selection graph node, and add it to the graph """
        sgnode = SGNode(name)
        sgnode.add_inputs(*args)
        sgnode.value = value
        sgnode.block = self.current_block
        self.sgraph.add_node(sgnode)
        return sgnode

    def add_map(self, node, sgvalue):
        assert isinstance(node, ir.Value)
        assert isinstance(sgvalue, SGValue)
        self.function_info.value_map[node] = sgvalue

    def get_value(self, node):
        value = self.function_info.value_map[node]
        if self.current_block is node.block or node.block is None or value.node.name.startswith('CONST'):
            pass
        else:
            print(node, node.block)
            if not value.vreg:
                value.vreg = self.function_info.frame.new_virtual_register(value.name)
        return value

    @register(ir.Return)
    def do_return(self, node):
        """ Move result into result register and jump to epilog """
        res = self.get_value(node.result)
        vreg = self.function_info.frame.rv
        opcode = make_opcode('MOV', node.result.ty)
        mov_node = self.new_node(opcode, res, value=vreg)
        self.chain(mov_node)

        # Jump to epilog:
        sgnode = self.new_node('JMP')
        sgnode.value = self.function_info.label_map[node.function.epilog]
        self.chain(sgnode)

    @register(ir.CJump)
    def do_cjump(self, node):
        """ Process conditional jump into dag """
        a = self.get_value(node.a)
        b = self.get_value(node.b)
        op = node.cond
        sgnode = self.new_node('CJMP', a, b)
        sgnode.value = op, self.function_info.label_map[node.lab_yes],\
            self.function_info.label_map[node.lab_no]
        self.chain(sgnode)

    @register(ir.Terminator)
    def do_terminator(self, node):
        sgnode = self.new_node('TRM')
        sgnode.add_input(self.current_token)

    @register(ir.Alloc)
    def do_alloc(self, node):
        # TODO: check alignment?
        fp = self.new_node("REGI32", value=self.function_info.frame.fp)
        fp_output = fp.new_output('fp')
        offset = self.new_node("CONSTI32")
        offset.value = self.function_info.frame.alloc_var(node, node.amount)
        offset_output = offset.new_output('offset')
        sgnode = self.new_node('ADDI32', fp_output, offset_output)
        self.chain(sgnode)
        self.add_map(node, sgnode.new_output('alloc'))

    def get_address(self, ir_address):
        """ Determine address for load or store. """
        if isinstance(ir_address, ir.Variable):
            # A global variable may be contained in another module
            # That is why it is created here, and not in the prepare step
            sgnode = self.new_node('LABEL', value=ir.label_name(ir_address))
            address = sgnode.new_output('address')
        else:
            address = self.get_value(ir_address)
        return address

    @register(ir.Load)
    def do_load(self, node):
        """ Create dag node for load operation """
        address = self.get_address(node.address)
        sgnode = self.new_node('LDR' + type_postfix(node.ty), address)
        # Make sure a data dependence is added to this node
        self.chain(sgnode)
        self.add_map(node, sgnode.new_output(node.name))

    @register(ir.Store)
    def do_store(self, node):
        """ Create a DAG node for the store operation """
        address = self.get_address(node.address)
        value = self.get_value(node.value)
        opcode = 'STR' + type_postfix(node.value.ty)
        sgnode = self.new_node(opcode, address, value)
        self.chain(sgnode)

    @register(ir.Const)
    def do_const(self, node):
        if isinstance(node.value, int):
            name = 'CONSTI32'
            value = node.value
        else:  # pragma: no cover
            raise NotImplementedError(str(type(node.value)))
        sgnode = self.new_node(name)
        sgnode.value = value
        self.add_map(node, sgnode.new_output(node.name))

    @register(ir.LiteralData)
    def do_literal_data(self, node):
        """ Literal data is stored after a label """
        label = self.function_info.frame.add_constant(node.data)
        sgnode = self.new_node('LABEL', value=label)
        self.add_map(node, sgnode.new_output(node.name))

    @register(ir.Binop)
    def do_binop(self, node):
        """ Visit a binary operator and create a DAG node """
        names = {'+': 'ADD', '-': 'SUB', '|': 'OR', '<<': 'SHL',
                 '*': 'MUL', '&': 'AND', '>>': 'SHR', '/': 'DIV',
                 '%': 'REM', '^': 'XOR'}
        op = names[node.operation] + type_postfix(node.ty)
        a = self.get_value(node.a)
        b = self.get_value(node.b)
        sgnode = self.new_node(op, a, b)
        self.add_map(node, sgnode.new_output(node.name))

    @register(ir.IntToByte)
    def do_int_to_byte_cast(self, node):
        # TODO: add some logic here?
        value = self.get_value(node.src)
        self.add_map(node, value)

    @register(ir.ByteToInt)
    def do_byte_to_int_cast(self, node):
        # TODO: add some logic here?
        value = self.get_value(node.src)
        self.add_map(node, value)

    @register(ir.IntToPtr)
    def do_int_to_ptr_cast(self, node):
        # TODO: add some logic here?
        value = self.get_value(node.src)
        self.add_map(node, value)

    @register(ir.PtrToInt)
    def do_ptr_to_int_cast(self, node):
        # TODO: add some logic here?
        value = self.get_value(node.src)
        self.add_map(node, value)

    @register(ir.Call)
    def do_call(self, node):
        # This is the moment to move all parameters to new temp registers.
        args = []
        inputs = []
        for argument in node.arguments:
            a = self.get_value(argument)
            loc = self.function_info.frame.new_virtual_register()
            args.append(loc)
            arg_sgnode = self.new_node('MOVI32', a, value=loc)
            self.chain(arg_sgnode)
            # inputs.append(arg_sgnode.new_output('x'))

        # New register for copy of result:
        ret_val = self.function_info.frame.new_virtual_register()

        # Perform the actual call:
        sgnode = self.new_node(
            'CALL', value=(node.function_name, args, ret_val))
        for i in inputs:
            sgnode.add_input(i)
        self.chain(sgnode)

        # When using the call as an expression, use copy of return value:
        output = sgnode.new_output('res')
        output.vreg = ret_val
        self.add_map(node, output)

    @register(ir.Phi)
    def do_phi(self, node):
        """ Refer to the correct copy of the phi node """
        vreg = self.function_info.phi_map[node]
        sgnode = self.new_node('REGI32', value=vreg)
        output = sgnode.new_output(node.name)
        output.vreg = vreg
        self.add_map(node, output)

    def copy_phis_of_successors(self, ir_block):
        """ When a terminator instruction is encountered, handle the copy
        of phi values into the expected virtual register """
        # Copy values to phi nodes in other blocks:
        for succ_block in ir_block.successors:
            for phi in succ_block.phis:
                vreg = self.function_info.phi_map[phi]
                from_val = phi.get_value(ir_block)
                val = self.get_value(from_val)
                opcode = make_opcode('MOV', phi.ty)
                sgnode = self.new_node(opcode, val, value=vreg)
                self.chain(sgnode)

    def entry_block_special_case(self, function_info, ir_function):
        """ Copy arguments into new temporary registers """
        # TODO: maybe this can be done different
        # Copy parameters into fresh temporaries:
        for arg in ir_function.arguments:
            param_node = self.new_node(
                'REGI32', value=function_info.frame.arg_loc(arg.num))
            assert isinstance(param_node.value, Register)
            output = param_node.new_output(arg.name)
            vreg = function_info.frame.new_virtual_register(twain=arg.name)
            output.vreg = vreg
            self.chain(param_node)

            # When refering the paramater, use the copied value:
            self.add_map(arg, output)

    def block_to_sgraph(self, ir_block, function_info):
        """ Create dag (directed acyclic graph) from a basic block.
            The resulting dag can be used for instruction selection.
        """
        assert isinstance(ir_block, ir.Block)
        self.logger.debug('Creating dag for {}'.format(ir_block.name))

        self.current_block = ir_block

        # Create start node:
        self.current_token = self.new_node('ENTRY').new_output(
            'token', kind=SGValue.CONTROL)

        # Emit extra dag for parameters when entry block:
        if ir_block is ir_block.function.entry:
            self.entry_block_special_case(function_info, ir_block.function)

        # Generate series of trees:
        for instruction in ir_block:
            # In case of last statement, first perform phi-lifting:
            if isinstance(instruction, ir.LastStatement):
                self.copy_phis_of_successors(ir_block)

            # Dispatch the handler depending on type:
            self.f_map[type(instruction)](self, instruction)

        # Create end node:
        sgnode = self.new_node('EXIT')
        sgnode.add_input(self.current_token)
        function_info.block_roots[ir_block] = sgnode

    def build(self, ir_function, function_info):
        """ Create a selection graph for the given function """
        self.sgraph = SelectionGraph()
        self.function_info = function_info

        # TODO: fix this total mess with vreg, block and chains:
        self.current_block = None

        # Create maps for global variables:
        for variable in ir_function.module.Variables:
            val = self.new_node('LABEL', value=ir.label_name(variable))
            self.add_map(variable, val.new_output(variable.name))

        # Create start node:
        self.current_token = self.new_node('ENTRY').new_output(
            'token', kind=SGValue.CONTROL)

        # Generate nodes for all blocks:
        for ir_block in ir_function:
            self.block_to_sgraph(ir_block, function_info)

        self.sgraph.check()
        return self.sgraph
