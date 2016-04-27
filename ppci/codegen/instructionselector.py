"""
    Instruction selector. This part of the compiler takes in a DAG (directed
    acyclic graph) of instructions and selects the proper target instructions.

    Selecting instructions from a DAG is a NP-complete problem. The simplest
    strategy is to split the DAG into a forest of trees and match these
    trees.

    Another solution may be: PBQP (Partitioned Boolean Quadratic Programming)
"""

import logging
from ..utils.tree import Tree
from .treematcher import State
from .. import ir
from .burg import BurgSystem
from .irdag import DagSplitter
from .irdag import FunctionInfo, prepare_function_info


size_classes = [8, 16, 32, 64]
ops = [
    'ADD', 'SUB', 'MUL', 'DIV', 'REM',
    'OR', 'SHL', 'SHR', 'AND', 'XOR',
    'MOV', 'REG', 'LDR', 'STR', 'CONST']

# Add all possible terminals:

terminals = tuple(x + 'I' + str(y) for x in ops for y in size_classes) + (
             "CALL", "LABEL",
             "JMP", "CJMP",
             "EXIT", "ENTRY")


class InstructionContext:
    """ Usable to patterns when emitting code """
    def __init__(self, frame, target, debug_db):
        self.frame = frame
        self.target = target
        self.debug_db = debug_db
        self.tree = None

    def new_reg(self, cls):
        """ Generate a new temporary of a given class """
        return self.frame.new_reg(cls)

    def move(self, dst, src):
        """ Generate move """
        self.emit(self.target.move(dst, src))

    def gen_call(self, label, arg_types, res_type, args, res_var):
        """ generate call for function into self """
        for instruction in self.target.gen_call(
                label, arg_types, res_type, args, res_var):
            self.emit(instruction)

    def emit(self, *args, **kwargs):
        """ Abstract instruction emitter proxy """
        instruction = self.frame.emit(*args, **kwargs)
        if self.tree:
            self.debug_db.map(self.tree, instruction)
        return instruction


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
            raise RuntimeError("Tree {} not covered".format(tree))
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

                # Check for acceptance:
                if rule.acceptance:
                    accept = rule.acceptance(tree)
                else:
                    accept = True

                if all(x.state.has_goal(y) for x, y in zip(kids, nts)) \
                        and accept:
                    cost = sum(x.state.get_cost(y) for x, y in zip(kids, nts))
                    cost = cost + rule.cost
                    tree.state.set_cost(rule.non_term, cost, rule.nr)

                    # Also set cost for chain rules here:
                    for cr in self.sys.chain_rules_for_nt(rule.non_term):
                        tree.state.set_cost(cr.non_term, cost + cr.cost, cr.nr)

    def apply_rules(self, context, tree, goal):
        """ Apply all selected instructions to the tree """
        rule = tree.state.get_rule(goal)
        results = [self.apply_rules(context, kid_tree, kid_goal)
                   for kid_tree, kid_goal in
                   zip(self.kids(tree, rule), self.nts(rule))]
        # Get the function to call:
        rule_f = self.sys.get_rule(rule).template
        context.tree = tree
        res = rule_f(context, tree, *results)
        context.tree = None
        return res

    def kids(self, tree, rule):
        """ Determine the kid trees for a rule """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_kids(tree, template_tree)

    def nts(self, rule):
        """ Get the open ends of this rules pattern """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_nts(template_tree)


class InstructionSelector1:
    """ Instruction selector which takes in a DAG and puts instructions
        into a frame.

        This one does selection and scheduling combined.
    """
    def __init__(self, isa, arch, sgraph_builder, debug_db):
        self.logger = logging.getLogger('instruction-selector')
        self.dag_builder = sgraph_builder
        self.arch = arch
        self.debug_db = debug_db
        self.dag_splitter = DagSplitter(arch, debug_db)

        # Generate burm table of rules:
        self.sys = BurgSystem()

        # Allow register results as root rule:
        # by adding a chain rule 'stm -> reg'
        # TODO: chain rules or register classes as root?
        self.sys.add_rule('stm', Tree('reg'), 0, None, lambda ct, tr, rg: None)
        self.sys.add_rule(
            'stm', Tree('reg64'), 0, None, lambda ct, tr, rg: None)

        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Add all isa patterns:
        for pattern in isa.patterns:
            cost = pattern.size + pattern.cycles + pattern.energy
            self.sys.add_rule(
                pattern.non_term, pattern.tree, cost,
                pattern.condition, pattern.method)

        self.sys.check()
        self.tree_selector = TreeSelector(self.sys)

    def select(self, ir_function, frame, reporter):
        """ Select instructions of function into a frame """
        assert isinstance(ir_function, ir.Function)
        self.logger.debug('Creating selection dag for %s', ir_function.name)

        # Create a object that carries global function info:
        function_info = FunctionInfo(frame)
        prepare_function_info(self.arch, function_info, ir_function)

        # Create a context that can emit instructions:
        context = InstructionContext(frame, self.arch, self.debug_db)

        # Create selection dag (directed acyclic graph):
        sgraph = self.dag_builder.build(ir_function, function_info)
        reporter.message('Selection graph for {}'.format(ir_function))
        reporter.dump_sgraph(sgraph)

        # Split the selection graph into trees:
        self.dag_splitter.split_into_trees(sgraph, ir_function, function_info)
        reporter.dump_trees(ir_function, function_info)

        # Process one basic block at a time:
        for ir_block in ir_function:
            # emit label of block:
            context.emit(function_info.label_map[ir_block])

            # Eat dag:
            trees = function_info.block_trees[ir_block]
            self.munch_trees(context, trees)

            # Emit code between blocks:
            frame.between_blocks()

        # Generate code for return statement:
        # TODO: return value must be implemented in some way..
        # self.munchStm(ir.Move(self.frame.rv, f.return_value))

    def munch_trees(self, context, trees):
        """ Consume a dag and match it using the matcher to the frame.
            DAG matching is NP-complete.

            The simplest strategy is to
            split the dag into a forest of trees. Then, the DAG is reduced
            to only trees, which can be matched.

            A different approach is use 0-1 programming, like the NOLTIS algo.

            TODO: implement different strategies.
        """

        # Match all splitted trees:
        for tree in trees:
            # Invoke dynamic programming matcher machinery:
            self.tree_selector.gen(context, tree)
