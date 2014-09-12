
import logging

from . import ir
from .target.basetarget import Label
from .irmach import AbstractInstruction, VirtualRegister
from .tree import Tree


class SelectionDagNode:
    def __init__(self):
        pass


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


@make_map
class Dagger:
    def __init__(self):
        self.logger = logging.getLogger('dag-creator')

    @register(ir.Jump)
    def do_jump(self, node):
        tree = Tree('JMP')
        label_name = ir.label_name(node.target)
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
        address = self.lut[node.address]
        tree = Tree('MEMI32', address)
        self.lut[node] = tree

    @register(ir.Store)
    def do_store(self, node):
        address = self.lut[node.address]
        value = self.lut[node.value]
        tree = Tree('MOVI32', Tree('MEMI32', address), value)
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
        op = names[node.operation] + str(node.ty).upper()
        assert node.ty == ir.i32
        a = self.lut[node.a]
        b = self.lut[node.b]
        tree = Tree(op, a, b)
        # Check if this binop is used more than once
        # if so, create register copy:
        if node.use_count > 1:
            rv_copy = Tree('REGI32', value=self.frame.new_virtual_register())
            self.dag.append(Tree('MOVI32', rv_copy, tree))
            self.lut[node] = rv_copy
        else:
            self.lut[node] = tree

    @register(ir.Addr)
    def do_addr(self, node):
        tree = Tree('ADR', self.lut[node.e])
        self.lut[node] = tree

    @register(ir.GlobalVariable)
    def do_global(self, node):
        """ This tree is put into the lut for later use """
        tree = Tree('GLOBALADDRESS', value=ir.label_name(node))
        self.lut[node] = tree

    @register(ir.Call)
    def do_call(self, node):
        # This is the moment to move all parameters correctly!
        # For each argument get the frame location and introduce a move
        # instruction.
        reg_uses = []
        for i, argument in enumerate(node.arguments):
            a = self.lut[argument]
            loc = self.frame.argLoc(i)
            loc_tree = Tree('REGI32', value=loc)
            reg_uses.append(loc)
            self.dag.append(Tree('MOVI32', loc_tree, a))

        # Perform the actual call:
        tree = Tree('CALL', value=(node.function_name, reg_uses))
        self.dag.append(tree)

        # Store return value:
        rv = Tree('REGI32', value=self.frame.rv)
        rv_copy = Tree('REGI32', value=self.frame.new_virtual_register())
        self.dag.append(Tree('MOVI32', rv_copy, rv))
        self.lut[node] = rv_copy
        # self.dag.append(Tree('MOVI32',

    @register(ir.Phi)
    def do_phi(self, node):
        # Phis are lifted elsewhere..
        # Create a new vreg for this phi:
        # The incoming branches provided with a copy instruction further on.
        rv_copy = Tree('REGI32', value=self.frame.new_virtual_register())
        self.lut[node] = rv_copy

    def only_arith(self, root):
        """ Determine if a tree is only arithmatic all the way up """
        return root.name in ['REGI32', 'ADDI32', 'SUBI32'] and all(self.only_arith(c) for c in root.children)

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

        # Move paramters into registers:
        # parmoves = []
        for p in irfunc.arguments:
            # TODO: pt = newTemp()
            # frame.parMap[p] = pt
            # parmoves.append(ir.Move(pt, frame.argLoc(p.num)))
            tree = Tree('REGI32', value=frame.argLoc(p.num))
            assert type(tree.value) is VirtualRegister
            self.lut[p] = tree

        # First define labels:
        for block in irfunc:
            block.dag = []
            label_name = ir.label_name(block)
            itgt = AbstractInstruction(Label(label_name))
            frame.label_map[label_name] = itgt
            block.dag.append(itgt)
            dags.append(block.dag)

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
