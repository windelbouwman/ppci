"""
    Instruction selector. This part of the compiler takes in a DAG (directed
    acyclic graph) of instructions and selects the proper target instructions.

    Selecting instructions from a DAG is a NP-complete problem. The simplest
    strategy is to split the DAG into a forest of trees and match these
    trees.
"""

from ..target.isa import Instruction
from .tree import State
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
        # Generate burm table of rules:
        self.sys = BurgSystem()

        # Add all possible terminals:
        terminals = ["ADDI32", "SUBI32", "MULI32",
                     "DIVI32", 'REMI32',
                     "ADR", "ORI32", "SHLI32",
                     "SHRI32", "ANDI32", "XORI32",
                     "CONSTI32",
                     "CONSTDATA",
                     "MEMI32",
                     "REGI32",
                     "MOVI16", "MEMI16",
                     "ADDI16", "SUBI16",
                     "MOVI8", "MEMI8",
                     "ADDI8", "SUBI8",
                     "CALL", "GLOBALADDRESS",
                     "MOVI32", "JMP", "CJMP"]
        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Add all isa patterns:
        for pattern in isa.patterns:
            self.sys.add_rule(
                pattern.non_term, pattern.tree, pattern.cost,
                pattern.condition, pattern.method)

        self.sys.check()
        self.tree_selector = TreeSelector(self.sys)

    def munch_dag(self, dags, frame):
        """ Consume a dag and match it using the matcher to the frame """
        # Entry point for instruction selection
        context = InstructionContext(frame)

        # TODO: split dag into forest!

        # Template match all trees:
        for dag in dags:
            for root in dag:
                if isinstance(root, Instruction):
                    # print(root)
                    context.emit(root)
                else:
                    # Invoke dynamic programming matcher machinery:
                    self.tree_selector.gen(context, root)
            frame.between_blocks()
