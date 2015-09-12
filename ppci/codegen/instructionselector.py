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
from ppci.pyburg import BurgSystem


# Add all possible terminals:
terminals = ("ADDI32", "SUBI32", "MULI32", "DIVI32", 'REMI32',
             "ADDI16", "SUBI16", "MULI16", "DIVI16", "REMI16",
             "ADDI8", "SUBI8", "MULI8", "DIVI8", 'REMI8',
             "ORI32", "SHLI32", "SHRI32", "ANDI32", "XORI32",
             "ORI16", "SHLI16", "SHRI16", "ANDI16", "XORI16",
             "ORI8", "SHLI8", "SHRI8", "ANDI8", "XORI8",
             "MOVI32", "REGI32", "LDRI32", "STRI32",
             "MOVI16", "REGI16", "LDRI16", "STRI16",
             "MOVI8", "REGI8", "LDRI8", "STRI8",
             "CONSTI32",
             "CONSTI16",
             'CONSTI8',
             "CALL", "LABEL",
             "JMP", "CJMP",
             "EXIT", "ENTRY")


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


def make_op(op, vreg):
    typ = 'I{}'.format(vreg.bitsize)
    return '{}{}'.format(op, typ)


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
        return rule_f(context, tree, *results)

    def kids(self, tree, rule):
        """ Determine the kid trees for a rule """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_kids(tree, template_tree)

    def nts(self, rule):
        """ Get the open ends of this rules pattern """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_nts(template_tree)


class DagSplitter:
    """ Class that splits a DAG into a series of trees. This series is sorted
        such that data dependencies are met. The trees can henceforth be
        used to match trees.
    """
    def __init__(self):
        self.logger = logging.getLogger('dag-splitter')

    def traverse_back(self, node):
        """
        Traverse the graph backwards from the given node, creating a tree
        and optionally adding this tree to the list of generated trees
        """

        # if node is already processed, stop:
        if node in self.node_map:
            return self.node_map[node]

        # Stop on entry node:
        if node.name == 'ENTRY':
            tree = Tree(node.name, value=node.value)
            self.node_map[node] = tree
            self.trees.append(tree)
            return tree

        # For now assert that nodes can only max 1 data value:
        assert len(node.data_outputs) <= 1

        # Make sure control dependencies are satisfied first:
        for inp in node.control_inputs:
            self.traverse_back(inp.node)

        # Second, process memory dependencies:
        for inp in node.memory_inputs:
            self.traverse_back(inp.node)

        # Create data for data dependencies:
        children = []
        for inp in node.data_inputs:
            if (inp.node.group is node.group) or \
                    (inp.node.group is None) or \
                    inp.node.name.startswith('CONST'):
                res = self.traverse_back(inp.node)
            else:
                if not inp.vreg:
                    vreg = self.frame.new_virtual_register(inp.name)
                    inp.vreg = vreg

            # If the input value has a vreg, use it:
            if inp.vreg:
                children.append(Tree(make_op('REG', inp.vreg), value=inp.vreg))
            else:
                children.append(res)

        # Create a tree node:
        tree = Tree(node.name, *children, value=node.value)

        # Determine if the node should be copied to register:
        for data_output in node.data_outputs:
            # Skip constants:
            if node.name.startswith('CONST'):
                continue

            # Check if value is used more then once:
            if (len(data_output.users) > 1) or node.volatile or \
                    any(u.group is not node.group for u in data_output.users):
                if not data_output.vreg:
                    vreg = self.frame.new_virtual_register(data_output.name)
                    data_output.vreg = vreg

        # Handle outputs:
        if len(node.data_outputs) == 0:
            # If the tree was volatile, it must be emitted
            if node.volatile:
                self.trees.append(tree)
        else:
            # If the output has a vreg, put the value in:
            data_output = node.data_outputs[0]
            if data_output.vreg:
                vreg = data_output.vreg
                tree = Tree(make_op('MOV', vreg), tree, value=vreg)
                self.trees.append(tree)
                tree = Tree(make_op('REG', vreg), value=vreg)
            elif node.volatile:
                self.trees.append(tree)

        # Store for later and prevent multi coverage of dag:
        self.node_map[node] = tree

        return tree

    def split_dag(self, root, frame):
        """ Split dag into forest of trees.
            The approach here is to start at the exit of the flowgraph
            and go back to the beginning.

            This function can be looped over and yields a series
            of somehow topologically sorted trees.
        """
        self.trees = []
        self.node_map = {}
        self.frame = frame

        assert len(root.outputs) == 0

        # First determine the usages:
        self.traverse_back(root)

        return self.trees


class InstructionSelector1:
    """ Instruction selector which takes in a DAG and puts instructions
        into a frame.

        This one does selection and scheduling combined.
    """
    def __init__(self, isa, dag_builder):
        self.dag_builder = dag_builder
        self.dag_splitter = DagSplitter()
        self.logger = logging.getLogger('instruction-selector')

        # Generate burm table of rules:
        self.sys = BurgSystem()

        # Allow register results as root rule:
        # by adding a chain rule 'stm -> reg'
        self.sys.add_rule('stm', Tree('reg'), 0, None, lambda ct, tr, rg: None)

        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Add all isa patterns:
        for pattern in isa.patterns:
            self.sys.add_rule(
                pattern.non_term, pattern.tree, pattern.cost,
                pattern.condition, pattern.method)

        self.sys.check()
        self.tree_selector = TreeSelector(self.sys)

    def munch_dag(self, context, root, reporter):
        """ Consume a dag and match it using the matcher to the frame.
            DAG matching is NP-complete.

            The simplest strategy is to
            split the dag into a forest of trees. Then, the DAG is reduced
            to only trees, which can be matched.

            A different approach is use 0-1 programming, like the NOLTIS algo.

            TODO: implement different strategies.
        """

        # Match all splitted trees:
        for tree in self.dag_splitter.split_dag(root, context.frame):
            reporter.message(str(tree))

            if tree.name in ['EXIT', 'ENTRY']:
                continue

            # Invoke dynamic programming matcher machinery:
            self.tree_selector.gen(context, tree)

    def select(self, ir_function, frame, function_info, reporter):
        """ Select instructions of function into a frame """
        assert isinstance(ir_function, ir.Function)
        self.logger.debug(
            'Creating selection dag for {}'.format(ir_function.name))

        # Create a context that can emit instructions:
        context = InstructionContext(frame)

        # Create selection dag (directed acyclic graph):
        sdag = self.dag_builder.build(ir_function, function_info)

        reporter.message('Selection graph for {}'.format(ir_function))
        reporter.dump_sgraph(sdag)

        # Process one basic block at a time:
        for ir_block in ir_function:
            # emit label of block:
            context.emit(function_info.label_map[ir_block])

            # Eat dag:
            reporter.message(str(ir_block))
            root = function_info.block_roots[ir_block]
            self.munch_dag(context, root, reporter)

            # Emit code between blocks:
            frame.between_blocks()

        # Generate code for return statement:
        # TODO: return value must be implemented in some way..
        # self.munchStm(ir.Move(self.frame.rv, f.return_value))
