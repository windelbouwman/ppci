"""
    The process of instruction selection is preceeded by the creation of
    a selection dag (directed acyclic graph). The dagger take ir-code as
    input and produces such a dag for instruction selection.

    A DAG represents the logic (computation) of a single basic block.
"""

import logging
from .. import ir
from ..utils.tree import Tree
from ..target.isa import Register
from ..target.target import Label


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


class Dag:
    """ Directed acyclic graph of to be selected instructions """
    def __init__(self):
        self.roots = []

    def get_node(self, value):
        return self.lut[value]

    def add_node(self, node):
        pass


class DagNode:
    def __init__(self, name, children=()):
        self.name = name
        self.children = children
        self.deps = []


class FunctionInfo:
    """ Keeps track of global function data when generating code for part
    of a functions. """
    def __init__(self, frame):
        self.frame = frame
        self.value_map = {}  # mapping from ir-value to dag node
        self.label_map = {}


@make_map
class DagBuilder:
    def __init__(self):
        self.logger = logging.getLogger('dag-builder')

    @register(ir.Jump)
    def do_jump(self, node):
        tree = Tree('JMP')
        tree.value = self.function_info.label_map[node.target]
        self.dag.append(tree)

    @register(ir.Return)
    def do_return(self, node):
        """ Move result into result register and jump to epilog """
        res = self.function_info.value_map[node.result]
        rv = Tree("REGI32", value=self.function_info.frame.rv)
        self.dag.append(Tree('MOVI32', rv, res))

        # Jump to epilog:
        tree = Tree('JMP')
        tree.value = self.function_info.label_map[node.function.epilog]
        self.dag.append(tree)

    @register(ir.CJump)
    def do_cjump(self, node):
        """ Process conditional jump into dag """
        a = self.function_info.value_map[node.a]
        b = self.function_info.value_map[node.b]
        op = node.cond
        tree = Tree('CJMP', a, b)
        tree.value = op, self.function_info.label_map[node.lab_yes],\
            self.function_info.label_map[node.lab_no]
        self.dag.append(tree)

    @register(ir.Terminator)
    def do_terminator(self, node):
        pass

    @register(ir.Alloc)
    def do_alloc(self, node):
        fp = Tree("REGI32", value=self.function_info.frame.fp)
        offset = Tree("CONSTI32")
        # TODO: check alignment?
        offset.value = self.function_info.frame.alloc_var(node, node.amount)
        tree = Tree('ADDI32', fp, offset)
        self.function_info.value_map[node] = tree

    @register(ir.Load)
    def do_load(self, node):
        """ Create dag node for load operation """
        if isinstance(node.address, ir.Variable):
            # A global variable may be contained in another module
            # That is why it is created here, and not in the prepare step
            address = Tree('GLOBALADDRESS', value=ir.label_name(node.address))
        else:
            address = self.function_info.value_map[node.address]
        tree = Tree('LDR' + type_postfix(node.ty), address)

        # Copy load always to register:
        vreg = self.function_info.frame.new_virtual_register()
        reg_tree = Tree('REGI32', value=vreg)
        self.dag.append(Tree('MOVI32', reg_tree, tree))

        self.function_info.value_map[node] = reg_tree

    @register(ir.Store)
    def do_store(self, node):
        """ Create a DAG node for the store operation """
        address = self.function_info.value_map[node.address]
        value = self.function_info.value_map[node.value]
        tree = Tree('STR' + type_postfix(node.value.ty), address, value)
        self.dag.append(tree)

    @register(ir.Const)
    def do_const(self, node):
        if isinstance(node.value, bytes):
            tree = Tree('CONSTDATA')
            tree.value = node.value
        elif isinstance(node.value, int):
            tree = Tree('CONSTI32')
            tree.value = node.value
        elif isinstance(node.value, bool):
            tree = Tree('CONSTI32')
            tree.value = int(node.value)
        else:  # pragma: no cover
            raise NotImplementedError(str(type(node.value)))
        self.function_info.value_map[node] = tree

    @register(ir.Binop)
    def do_binop(self, node):
        """ Visit a binary operator and create a DAG node """
        names = {'+': 'ADD', '-': 'SUB', '|': 'OR', '<<': 'SHL',
                 '*': 'MUL', '&': 'AND', '>>': 'SHR', '/': 'DIV',
                 '%': 'REM', '^': 'XOR'}
        op = names[node.operation] + type_postfix(node.ty)
        a = self.function_info.value_map[node.a]
        b = self.function_info.value_map[node.b]
        tree = Tree(op, a, b)
        self.function_info.value_map[node] = tree

    @register(ir.Addr)
    def do_addr(self, node):
        tree = Tree('ADR', self.function_info.value_map[node.e])
        self.function_info.value_map[node] = tree

    @register(ir.IntToByte)
    def do_int_to_byte_cast(self, node):
        # TODO: add some logic here?
        value = self.function_info.value_map[node.src]
        self.function_info.value_map[node] = value

    @register(ir.ByteToInt)
    def do_byte_to_int_cast(self, node):
        # TODO: add some logic here?
        value = self.function_info.value_map[node.src]
        self.function_info.value_map[node] = value

    @register(ir.IntToPtr)
    def do_int_to_ptr_cast(self, node):
        # TODO: add some logic here?
        value = self.function_info.value_map[node.src]
        self.function_info.value_map[node] = value

    @register(ir.PtrToInt)
    def do_ptr_to_int_cast(self, node):
        # TODO: add some logic here?
        value = self.function_info.value_map[node.src]
        self.function_info.value_map[node] = value

    @register(ir.Call)
    def do_call(self, node):
        # This is the moment to move all parameters to new temp registers.
        args = []
        for argument in node.arguments:
            a = self.function_info.value_map[argument]
            loc = self.function_info.frame.new_virtual_register()
            loc_tree = Tree('REGI32', value=loc)
            args.append(loc)
            self.dag.append(Tree('MOVI32', loc_tree, a))

        # New register for copy of result:
        ret_val = self.function_info.frame.new_virtual_register()

        # Perform the actual call:
        tree = Tree('CALL', value=(node.function_name, args, ret_val))
        self.dag.append(tree)

        # When using the call as an expression, use copy of return value:
        self.function_info.value_map[node] = Tree('REGI32', value=ret_val)

    @register(ir.Phi)
    def do_phi(self, node):
        """ Phis are lifted elsewhere. """
        pass

    def only_arith(self, root):
        """ Determine if a tree is only arithmatic all the way up """
        return root.name in ['REGI32', 'ADDI32', 'SUBI32'] and \
            all(self.only_arith(c) for c in root.children)

    def copy_phis_of_successors(self, ir_block):
        """ When a terminator instruction is encountered, handle the copy
        of phi values into the expected virtual register """
        # Copy values to phi nodes in other blocks:
        for succ_block in ir_block.successors:
            for phi in succ_block.phis:
                vreg = self.function_info.value_map[phi]
                from_val = phi.get_value(ir_block)
                val = self.function_info.value_map[from_val]
                tree = Tree('MOVI32', vreg, val)
                self.dag.append(tree)

    def entry_block_special_case(self, function_info, dag, ir_function):
        # TODO: maybe this can be done different
        # Copy parameters into fresh temporaries:
        for arg in ir_function.arguments:
            param_tree = Tree(
                'REGI32', value=function_info.frame.arg_loc(arg.num))
            assert isinstance(param_tree.value, Register)
            vreg = function_info.frame.new_virtual_register(twain=arg.name)
            param_copy = Tree('REGI32', value=vreg)
            dag.append(Tree('MOVI32', param_copy, param_tree))
            # When refering the paramater, use the copied value:
            function_info.value_map[arg] = param_copy

    def prepare_function_info(self, function_info, ir_function):
        """ Fill function info with labels for all basic blocks """
        # First define labels and phis:
        for ir_block in ir_function:
            # Put label into map:
            function_info.label_map[ir_block] = Label(ir.label_name(ir_block))

            # Create phi virtual registers:
            for phi in ir_block.phis:
                vreg = function_info.frame.new_virtual_register(
                    twain=phi.name)
                phi_copy = Tree('REGI32', value=vreg)
                function_info.value_map[phi] = phi_copy

        # Construct trees for global variables:
        for global_variable in ir_function.module.Variables:
            tree = Tree('GLOBALADDRESS', value=ir.label_name(global_variable))
            function_info.value_map[global_variable] = tree

    def make_dag(self, ir_block, function_info):
        """ Create dag (directed acyclic graph) from a basic block.
            The resulting dag can be used for instruction selection.
        """
        assert isinstance(ir_block, ir.Block)
        self.logger.debug('Creating dag for {}'.format(ir_block.name))

        self.function_info = function_info
        self.dag = []

        # Emit extra dag for parameters when entry block:
        if ir_block is ir_block.function.entry:
            self.entry_block_special_case(
                function_info, self.dag, ir_block.function)

        # Generate series of trees:
        for instruction in ir_block:
            # In case of last statement, first perform phi-lifting:
            if isinstance(instruction, ir.LastStatement):
                self.copy_phis_of_successors(ir_block)
            self.f_map[type(instruction)](self, instruction)

        return self.dag
