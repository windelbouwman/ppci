
import logging

from . import ir
from .target.basetarget import Label
from .irmach import AbstractInstruction, VirtualRegister
from .tree import Tree


NODE_ATTR = '%nodetype'


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
    postfix_map = {ir.i32: "I32", ir.ptr: "I32", ir.i8: 'I8'}
    return postfix_map[typ]


@make_map
class Dagger:
    def __init__(self):
        self.logger = logging.getLogger('dag-creator')

    def copy_val(self, node, tree):
        """ Copy value into new temporary if node is used more than once """
        if node.use_count > 1:
            rv_copy = Tree('REGI32', value=self.frame.new_virtual_register())
            self.dag.append(Tree('MOVI32', rv_copy, tree))
            self.lut[node] = rv_copy
        else:
            self.lut[node] = tree

    @register(ir.Jump)
    def do_jump(self, node):
        tree = Tree('JMP')
        label_name = ir.label_name(node.target)
        tree.value = label_name, self.frame.label_map[label_name]
        self.dag.append(tree)

    @register(ir.Return)
    def do_return(self, node):
        """ Move result into result register and jump to epilog """
        res = self.lut[node.result]
        rv = Tree("REGI32", value=self.frame.rv)
        self.dag.append(Tree('MOVI32', rv, res))

        # Jump to epilog:
        tree = Tree('JMP')
        label_name = ir.label_name(node.function.epilog)
        tree.value = label_name, self.frame.label_map[label_name]
        self.dag.append(tree)

    @register(ir.CJump)
    def do_cjump(self, node):
        a = self.lut[node.a]
        b = self.lut[node.b]
        op = node.cond
        yes_label_name = ir.label_name(node.lab_yes)
        no_label_name = ir.label_name(node.lab_no)
        tree = Tree('CJMP', a, b)
        tree.value = op, yes_label_name, self.frame.label_map[yes_label_name],\
            no_label_name, self.frame.label_map[no_label_name]
        self.dag.append(tree)

    @register(ir.Terminator)
    def do_terminator(self, node):
        pass

    @register(ir.Alloc)
    def do_alloc(self, node):
        fp = Tree("REGI32", value=self.frame.fp)
        offset = Tree("CONSTI32")
        # TODO: check size and alignment?
        offset.value = self.frame.allocVar(node, node.amount)
        tree = Tree('ADDI32', fp, offset)
        self.lut[node] = tree

    @register(ir.Load)
    def do_load(self, node):
        if isinstance(node.address, ir.Variable):
            address = Tree('GLOBALADDRESS', value=ir.label_name(node.address))
        else:
            address = self.lut[node.address]
        tree = Tree('MEM' + type_postfix(node.ty), address)

        # Create copy if required:
        self.copy_val(node, tree)

    @register(ir.Store)
    def do_store(self, node):
        address = self.lut[node.address]
        value = self.lut[node.value]
        ty = type_postfix(node.value.ty)
        tree = Tree('MOV' + ty, Tree('MEM' + ty, address), value)
        self.dag.append(tree)

    @register(ir.Const)
    def do_const(self, node):
        if type(node.value) is bytes:
            tree = Tree('CONSTDATA')
            tree.value = node.value
        elif type(node.value) is int:
            tree = Tree('CONSTI32')
            tree.value = node.value
        elif type(node.value) is bool:
            tree = Tree('CONSTI32')
            tree.value = int(node.value)
        else:
            raise Exception('{} not implemented'.format(type(node.value)))
        self.lut[node] = tree

    @register(ir.Binop)
    def do_binop(self, node):
        names = {'+': 'ADD', '-': 'SUB', '|': 'OR', '<<': 'SHL',
                 '*': 'MUL', '&': 'AND', '>>': 'SHR'}
        op = names[node.operation] + type_postfix(node.ty)
        a = self.lut[node.a]
        b = self.lut[node.b]
        tree = Tree(op, a, b)

        # Check if this binop is used more than once
        # if so, create register copy:
        self.copy_val(node, tree)

    @register(ir.Addr)
    def do_addr(self, node):
        tree = Tree('ADR', self.lut[node.e])
        self.lut[node] = tree

    @register(ir.IntToByte)
    def do_int_to_byte_cast(self, node):
        # TODO: add some logic here?
        v = self.lut[node.src]
        self.lut[node] = v

    @register(ir.IntToPtr)
    def do_int_to_ptr_cast(self, node):
        # TODO: add some logic here?
        v = self.lut[node.src]
        self.lut[node] = v

    @register(ir.ByteToInt)
    def do_byte_to_int_cast(self, node):
        # TODO: add some logic here?
        v = self.lut[node.src]
        self.lut[node] = v

    @register(ir.Variable)
    def do_global(self, node):
        """ This tree is put into the lut for later use """
        tree = Tree('GLOBALADDRESS', value=ir.label_name(node))
        self.lut[node] = tree

    @register(ir.Call)
    def do_call(self, node):
        # This is the moment to move all parameters to new temp registers.
        args = []
        for argument in node.arguments:
            a = self.lut[argument]
            loc = self.frame.new_virtual_register()
            loc_tree = Tree('REGI32', value=loc)
            args.append(loc)
            self.dag.append(Tree('MOVI32', loc_tree, a))

        # New register for copy of result:
        rv = self.frame.new_virtual_register()

        # Perform the actual call:
        tree = Tree('CALL', value=(node.function_name, args, rv))
        self.dag.append(tree)

        # When using the call as an expression, use copy of return value:
        self.lut[node] = Tree('REGI32', value=rv)

    @register(ir.Phi)
    def do_phi(self, node):
        """
            Phis are lifted elsewhere..
        Create a new vreg for this phi:
        The incoming branches provided with a copy instruction further on.
        """
        phi_copy = Tree(
            'REGI32',
            value=self.frame.new_virtual_register(twain=node.name))
        self.lut[node] = phi_copy

    def only_arith(self, root):
        """ Determine if a tree is only arithmatic all the way up """
        return root.name in ['REGI32', 'ADDI32', 'SUBI32'] and \
            all(self.only_arith(c) for c in root.children)

    def split_dag(self, dag):
        """ Split dag into forest of trees """
        # self.
        for root in dag:
            print(root)

    def make_dag(self, irfunc, frame):
        """ Create dag (directed acyclic graph) of nodes for the selection
            this function makes a list of dags. One for each basic blocks.
            one dag is a list of trees.
        """
        assert isinstance(irfunc, ir.Function)
        self.logger.debug('Creating selection dag for {}'.format(irfunc.name))

        self.lut = {}
        self.frame = frame
        dags = []
        frame.label_map = {}

        # Construct trees for global variables:
        for global_variable in irfunc.module.Variables:
            self.f_map[type(global_variable)](self, global_variable)

        # First define labels:
        for block in irfunc:
            block.dag = []
            label_name = ir.label_name(block)
            itgt = AbstractInstruction(Label(label_name))
            frame.label_map[label_name] = itgt
            block.dag.append(itgt)
            dags.append(block.dag)

        # Copy parameters into fresh temporaries:
        entry_dag = irfunc.entry.dag
        for arg in irfunc.arguments:
            param_tree = Tree('REGI32', value=frame.arg_loc(arg.num))
            assert type(param_tree.value) is VirtualRegister
            param_copy = Tree('REGI32')
            param_copy.value = self.frame.new_virtual_register(twain=arg.name)
            entry_dag.append(Tree('MOVI32', param_copy, param_tree))
            # When refering the paramater, use the copied value:
            self.lut[arg] = param_copy

        # Generate series of trees for all blocks:
        for block in irfunc:
            self.dag = block.dag
            for instruction in block.Instructions:
                self.f_map[type(instruction)](self, instruction)

        self.logger.debug('Lifting phi nodes')
        # Construct out of SSA form (remove phi-s)
        # Lift phis, append them to end of incoming blocks..
        for block in irfunc:
            for instruction in block:
                if type(instruction) is ir.Phi:
                    # Add moves to incoming branches:
                    vreg = self.lut[instruction]
                    for from_block, from_val in instruction.inputs.items():
                        val = self.lut[from_val]
                        tree = Tree('MOVI32', vreg, val)
                        # Insert before jump (do not use append):
                        from_block.dag.insert(-1, tree)

        # Split dags into trees!
        self.logger.debug('Splitting forest')
        for dag in dags:
            for dg in dag:
                # self.split_dag(dg)
                pass

        # Generate code for return statement:
        # TODO: return value must be implemented in some way..
        # self.munchStm(ir.Move(self.frame.rv, f.return_value))

        return dags
