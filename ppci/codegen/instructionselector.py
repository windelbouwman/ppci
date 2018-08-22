""" Instruction selector.

This part of the compiler takes in a DAG (directed
acyclic graph) of instructions and selects the proper target instructions.

Selecting instructions from a DAG is a NP-complete problem. The simplest
strategy is to split the DAG into a forest of trees and match these
trees.

Another solution may be: PBQP (Partitioned Boolean Quadratic Programming)

The selection process creates operations in a selection DAG. The possible
operations are listed in the below table:

+---------------+---------+-----------------------------------------+
| operation     | types   | description                             |
+===============+=========+=========================================+
| ADD(c0,c1)    | I,U     | Add its operands                        |
+---------------+---------+-----------------------------------------+
| SUB(c0,c1)    | I,U     | Substracts c1 from c0                   |
+---------------+---------+-----------------------------------------+
| MUL(c0,c1)    | I,U     | Multiplies c0 by c1                     |
+---------------+---------+-----------------------------------------+
| DIV(c0,c1)    | I,U     | Divides c0 by c1                        |
+---------------+---------+-----------------------------------------+
| OR(c0,c1)     | I,U     | Bitwise or                              |
+---------------+---------+-----------------------------------------+
| AND(c0,c1)    | I,U     | Bitwise and                             |
+---------------+---------+-----------------------------------------+
| XOR(c0,c1)    | I,U     | Bitwise exclusive or                    |
+---------------+---------+-----------------------------------------+
| LDR(c0)       | I,U     | Load from memory                        |
+---------------+---------+-----------------------------------------+
| STR(c0,c1)    | I,U     | Store value c1 at memory address c0     |
+---------------+---------+-----------------------------------------+
| FPREL         | U       | Frame pointer relative location         |
+---------------+---------+-----------------------------------------+
| CONST         | I,U     | Constant value                          |
+---------------+---------+-----------------------------------------+
| REG           | I,U     | Value in a specific register            |
+---------------+---------+-----------------------------------------+
| JMP           | I,U     | Jump to a label                         |
+---------------+---------+-----------------------------------------+
| CJMP          | I,U     | Conditional jump to a label             |
+---------------+---------+-----------------------------------------+

...

Memory move operations:

- STRI64(REGI32[rax], CONSTI32[1])
- MOVB()


"""

import abc
import logging
from ..utils.tree import Tree
from .treematcher import State
from .. import ir
from ..arch.encoding import Instruction
from .burg import BurgSystem
from .irdag import FunctionInfo, prepare_function_info
from .dagsplit import DagSplitter
from ..arch.generic_instructions import RegisterUseDef


data_types = [str(t).upper() for t in ir.all_types]

ops = [
    'ADD', 'SUB', 'MUL', 'DIV', 'REM',  # Arithmatics
    'OR', 'SHL', 'SHR', 'AND', 'XOR',  # bitwise stuff
    'NEG', 'INV',  # Unary operations
    'MOV', 'REG', 'LDR', 'STR', 'CONST',  # Data
    'CJMP',  # Compare and jump
    'I8TO', 'I16TO', 'I32TO', 'I64TO',  # Conversions
    'U8TO', 'U16TO', 'U32TO', 'U64TO',
    'F32TO', 'F64TO',
    'FPREL', 'SPREL',  # Frame/stack pointer relative
    ]

# Add all possible terminals:

terminals = tuple(x + y for x in ops for y in data_types) + (
             "CALL", "LABEL",
             'MOVB',  # Attempts at blob data copies
             "JMP",
             "EXIT", "ENTRY",
             'ALLOCA', 'FREEA')


class ContextInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def emit(self, instruction):  # pragma: no cover
        raise NotImplementedError()


class InstructionContext(ContextInterface):
    """ Usable to patterns when emitting code """
    def __init__(self, frame, arch):
        self.frame = frame
        self.arch = arch
        self.debug_db = frame.debug_db
        self.tree = None

    def new_reg(self, cls):
        """ Generate a new temporary of a given class """
        return self.frame.new_reg(cls)

    def new_label(self):
        """ Generate a new unique label """
        return self.frame.new_label()

    def move(self, dst, src):
        """ Generate move """
        self.emit(self.arch.move(dst, src))

    def emit(self, instruction):
        """ Abstract instruction emitter proxy """
        self.frame.emit(instruction)
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
                    marked_rules = set()
                    self.mark_tree(tree, rule, cost, marked_rules)

    def mark_tree(self, tree, rule, cost, marked_rules):
        cost = cost + rule.cost
        tree.state.set_cost(rule.non_term, cost, rule.nr)
        marked_rules.add(rule)

        # Also set cost for chain rules here:
        for cr in self.sys.chain_rules_for_nt(rule.non_term):
            if cr not in marked_rules:
                self.mark_tree(tree, cr, cost, marked_rules)

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
    verbose = False

    def __init__(self, arch, sgraph_builder, weights=(1, 1, 1)):
        """ Create a new instruction selector.

        Weights can be given to select instructions given more for:
        - size
        - execution cycles
        - or energy
        respectively.
        """
        self.logger = logging.getLogger('instruction-selector')
        self.dag_builder = sgraph_builder
        self.arch = arch
        self.dag_splitter = DagSplitter(arch)

        # Generate burm table of rules:
        self.sys = BurgSystem()

        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Add special case nodes:
        self.sys.add_rule(
            'stm', Tree('CALL'), 0, None, self.call_function)

        # Add all isa patterns:
        for pattern in arch.isa.patterns:
            cost = pattern.size * weights[0] + \
                   pattern.cycles * weights[1] + \
                   pattern.energy * weights[2]
            self.sys.add_rule(
                pattern.non_term, pattern.tree, cost,
                pattern.condition, pattern.method)

        self.sys.check()
        self.tree_selector = TreeSelector(self.sys)

    def call_function(self, context, tree):
        label, args, rv = tree.value
        for instruction in self.arch.gen_call(context.frame, label, args, rv):
            context.emit(instruction)

    def memcp(self):
        """ Invoke memcpy arch function """
        for instruction in self.arch.gen_memcpy(dst, src, size):
            context.emit(instruction)

    def select(self, ir_function: ir.SubRoutine, frame, reporter):
        """ Select instructions of function into a frame """
        assert isinstance(ir_function, ir.SubRoutine)
        self.logger.debug('Creating selection dag for %s', ir_function.name)

        # Create a object that carries global function info:
        function_info = FunctionInfo(frame)
        prepare_function_info(self.arch, function_info, ir_function)

        # Create selection dag (directed acyclic graph):
        sgraph = self.dag_builder.build(
            ir_function, function_info, frame.debug_db)

        if self.verbose:
            # Graph drawing takes considerable time
            # only do this in verbose mode.
            reporter.dump_sgraph(sgraph)

        # Split the selection graph into a forest of trees:
        forest = self.dag_splitter.split_into_trees(
            sgraph, ir_function, function_info, frame.debug_db)
        reporter.dump_trees(forest)

        # Create a context that can emit instructions:
        context = InstructionContext(frame, self.arch)

        args = list(zip(function_info.arg_types, function_info.arg_vregs))
        for instruction in self.arch.gen_function_enter(args):
            context.emit(instruction)

        # Generate proper instructions:
        self.munch_trees(context, forest)

        # Generate function tail:
        if isinstance(ir_function, ir.Function):
            rv = (ir_function.return_ty, function_info.rv_vreg)
        else:
            rv = None

        for instruction in self.arch.gen_function_exit(rv):
            context.emit(instruction)

        # TODO!!!
        # Emit code between blocks:
        # for instruction in self.arch.between_blocks(frame):
        #    frame.emit(instruction)

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
            if isinstance(tree, Instruction):
                context.emit(tree)
            else:
                assert isinstance(tree, Tree)
                self.gen_tree(context, tree)

    def gen_tree(self, context, tree):
        """ Generate code from a tree """
        self.tree_selector.gen(context, tree)
