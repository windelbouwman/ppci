"""
    Instruction selector. This part of the compiler takes in a DAG (directed
    acyclic graph) of instructions and selects the proper target instructions.

    Selecting instructions from a DAG is a NP-complete problem. The simplest
    strategy is to split the DAG into a forest of trees and match these
    trees.
"""

import logging
from ..target.isa import Register
from ..utils.tree import Tree
from ..target.target import Label
from .irdag import DagBuilder, FunctionInfo
from .tree import State
from .. import ir
from ppci.pyburg import BurgSystem


class InstructionContext:
    """ Usable to patterns when emitting code """
    def __init__(self, frame):
        self.frame = frame

    def new_temp(self):
        """ Generate a new temporary """
        return self.frame.new_virtual_register()

    def move(self, dst, src):
        """ Generate move """
        self.frame.move(dst, src)

    def emit(self, *args, **kwargs):
        """ Abstract instruction emitter proxy """
        return self.frame.emit(*args, **kwargs)


class TreeSelector:
    """ Tree matcher that can match a tree and generate instructions """
    def __init__(self, sys):
        self.sys = sys

    def gen(self, context, tree):
        """ Generate code for a given tree. The tree will be tiled with
            patterns and the corresponding code will be emitted """
        self.sys.check_tree_defined(tree)
        self.burm_label(tree)
        if not tree.state.has_goal("stm"):  # pragma: no cover
            raise Exception("Tree {} not covered".format(tree))
        return self.apply_rules(context, tree, "stm")

    def burm_label(self, tree):
        """ Label all nodes in the tree bottom up """
        for child_tree in tree.children:
            self.burm_label(child_tree)

        # Now the child nodes have been labeled, assign a state to the tree:
        tree.state = State()

        # Check all rules for matching with this subtree and
        # check if a state can be determined
        for rule in self.sys.get_rules_for_root(tree.name):
            if self.sys.tree_terminal_equal(tree, rule.tree):
                nts = self.nts(rule.nr)
                kids = self.kids(tree, rule.nr)
                accept = True
                if rule.acceptance:
                    accept = rule.acceptance(tree)
                if all(x.state.has_goal(y) for x, y in zip(kids, nts)) \
                        and accept:
                    cost = sum(x.state.get_cost(y) for x, y in zip(kids, nts))
                    cost = cost + rule.cost
                    tree.state.set_cost(rule.non_term, cost, rule.nr)

                    # TODO: chain rules!!!

    def apply_rules(self, context, tree, goal):
        """ Apply all selected instructions to the tree """
        rule = tree.state.get_rule(goal)
        results = [self.apply_rules(context, kid_tree, kid_goal)
                   for kid_tree, kid_goal in
                   zip(self.kids(tree, rule), self.nts(rule))]
        # Get the function to call:
        rule_f = self.sys.get_rule(rule).template
        return rule_f(context, tree, *results)

    def kids(self, tree, rule):
        """ Determine the kid trees for a rule """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_kids(tree, template_tree)

    def nts(self, rule):
        """ Get the open ends of this rules pattern """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_nts(template_tree)


class InstructionSelector:
    """ Instruction selector which takes in a DAG and puts instructions
        into a frame.
    """
    def __init__(self, isa):
        self.dag_builder = DagBuilder()
        self.logger = logging.getLogger('instruction-selector')

        # Generate burm table of rules:
        self.sys = BurgSystem()

        # Add all possible terminals:
        terminals = ["ADDI32", "SUBI32", "MULI32", "DIVI32", 'REMI32',
                     "ADDI16", "SUBI16", "MULI16", "DIVI16", "REMI16",
                     "ADDI8", "SUBI8",
                     "ORI32", "SHLI32", "SHRI32", "ANDI32", "XORI32",
                     "ORI16", "SHLI16", "SHRI16", "ANDI16", "XORI16",
                     "ORI8", "SHLI8", "SHRI8", "ANDI8", "XORI8",
                     "MOVI32", "MEMI32", "REGI32",
                     "MOVI16", "MEMI16", "REGI16",
                     "MOVI8", "MEMI8", "REGI8",
                     "ADR",
                     "CONSTI32",
                     "CONSTDATA",
                     "CALL", "GLOBALADDRESS",
                     "JMP", "CJMP"]
        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Add all isa patterns:
        for pattern in isa.patterns:
            self.sys.add_rule(
                pattern.non_term, pattern.tree, pattern.cost,
                pattern.condition, pattern.method)

        self.sys.check()
        self.tree_selector = TreeSelector(self.sys)

    def split_dag(self, dag):
        """ Split dag into forest of trees """
        # self.
        for root in dag:
            print(root)

    def munch_dag(self, context, dag):
        """ Consume a dag and match it using the matcher to the frame """
        # TODO: split dag into forest!
        # Split dags into trees!
        self.logger.debug('Splitting forest')
        for dg in dag:
            # self.split_dag(dg)
            pass

        # Template match all trees:
        for root in dag:
            # Invoke dynamic programming matcher machinery:
            self.tree_selector.gen(context, root)

    def select(self, ir_function, frame):
        """ Select instructions of function into a frame """
        assert isinstance(ir_function, ir.Function)
        self.logger.debug(
            'Creating selection dag for {}'.format(ir_function.name))

        # Create a context that can emit instructions:
        context = InstructionContext(frame)

        # Create a function info that carries global function info:
        function_info = FunctionInfo(frame)

        # First define labels and phis:
        for ir_block in ir_function:
            ir_block.dag = []

            # Put label into map:
            label = Label(ir.label_name(ir_block))
            function_info.label_map[ir_block] = label

            # Create phi copy:
            for phi in ir_block.phis:
                phi_copy = Tree(
                    'REGI32',
                    value=frame.new_virtual_register(twain=phi.name))
                function_info.lut[phi] = phi_copy

        # Construct trees for global variables:
        for global_variable in ir_function.module.Variables:
            tree = Tree('GLOBALADDRESS', value=ir.label_name(global_variable))
            function_info.lut[global_variable] = tree

        # Copy parameters into fresh temporaries:
        entry_dag = ir_function.entry.dag
        for arg in ir_function.arguments:
            param_tree = Tree('REGI32', value=frame.arg_loc(arg.num))
            assert isinstance(param_tree.value, Register)
            param_copy = Tree('REGI32')
            param_copy.value = frame.new_virtual_register(twain=arg.name)
            entry_dag.append(Tree('MOVI32', param_copy, param_tree))
            # When refering the paramater, use the copied value:
            function_info.lut[arg] = param_copy

        # Process one basic block at a time:
        for ir_block in ir_function:
            # emit label of block:
            label = function_info.label_map[ir_block]
            context.emit(label)

            # Create selection dag (directed acyclic graph):
            dag = self.dag_builder.make_dag(ir_block, function_info)

            # Eat dag:
            self.munch_dag(context, dag)

            # Emit code between blocks:
            frame.between_blocks()

        # Generate code for return statement:
        # TODO: return value must be implemented in some way..
        # self.munchStm(ir.Move(self.frame.rv, f.return_value))
