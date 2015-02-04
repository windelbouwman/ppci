from ppci.irmach import AbstractInstruction
from ppci.tree import State, Tree, from_string
from ppci.pyburg import BurgSystem


def pattern(non_term, tree, cost=0):
    """
        Decorator function that marks the method as a pattern implementation
    """
    if type(tree) is str:
        tree = from_string(tree)

    assert type(tree) is Tree

    def wrapper(function):
        """
            Wrapper for function that does not modify function, but attaches
            the attributes tree and cost to it
        """
        setattr(function, '$non_term', non_term)
        setattr(function, '$tree', tree)
        setattr(function, '$cost', cost)
        return function
    return wrapper


class InstructionSelector:
    """
        Base instruction selector. This class must be inherited by
        backends.
    """
    def __init__(self):
        # Generate burm table of rules:
        self.sys = BurgSystem()

        # Add all possible terminals:
        terminals = ["ADDI32", "SUBI32", "MULI32",
                     "ADDI8", "SUBI8",
                     "ADR", "ORI32", "SHLI32",
                     "SHRI32", "ANDI32", "CONSTI32",
                     "CONSTDATA",
                     "MEMI32",
                     "REGI32",
                     "MOVI8", "MEMI8",
                     "CALL", "GLOBALADDRESS",
                     "MOVI32", "JMP", "CJMP"]
        for terminal in terminals:
            self.sys.add_terminal(terminal)

        # Find all member functions in the subclass:
        for name, method in self.__class__.__dict__.items():
            if hasattr(method, '$cost'):
                non_term = getattr(method, '$non_term')
                tree = getattr(method, '$tree')
                cost = getattr(method, '$cost')
                self.sys.add_rule(non_term, tree, cost, None, method)

        self.sys.check()

    def newTmp(self):
        return self.frame.new_virtual_register()

    def munch_dag(self, dags, frame):
        """ Consume a dag and match it using the matcher to the frame """
        # Entry point for instruction selection

        # Enter a frame per function:
        self.frame = frame

        # Template match all trees:
        for dag in dags:
            for root in dag:
                if type(root) is AbstractInstruction:
                    self.emit(root)
                else:
                    # Invoke dynamic programming matcher machinery:
                    self.gen(root)
            frame.between_blocks()

    def munchCall(self, e):
        """ Generate code for call sequence """
        label, args, res_var = e
        self.frame.gen_call(label, args, res_var)

    def move(self, dst, src):
        """ Generate move """
        self.frame.move(dst, src)

    def emit(self, *args, **kwargs):
        """ Abstract instruction emitter proxy """
        return self.frame.emit(*args, **kwargs)

    # Matcher parts:
    def gen(self, tree):
        """ Generate code for a given tree. The tree will be tiled with
            patterns and the corresponding code will be emitted """
        self.sys.check_tree_defined(tree)
        self.burm_label(tree)
        if not tree.state.has_goal("stm"):
            raise Exception("Tree {} not covered".format(tree))
        return self.apply_rules(tree, "stm")

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
                if all(x.state.has_goal(y) for x, y in zip(kids, nts)):
                    cost = sum(x.state.get_cost(y) for x, y in zip(kids, nts))
                    cost = cost + rule.cost
                    tree.state.set_cost(rule.non_term, cost, rule.nr)

                    # TODO: chain rules!!!

    def apply_rules(self, tree, goal):
        """ Apply all selected instructions to the tree """
        rule = tree.state.get_rule(goal)
        results = [self.apply_rules(kid_tree, kid_goal)
                   for kid_tree, kid_goal in
                   zip(self.kids(tree, rule), self.nts(rule))]
        # Get the function to call:
        rule_f = self.sys.get_rule(rule).template
        return rule_f(self, tree, *results)

    def kids(self, tree, rule):
        """ Determine the kid trees for a rule """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_kids(tree, template_tree)

    def nts(self, rule):
        """ Get the open ends of this rules pattern """
        template_tree = self.sys.get_rule(rule).tree
        return self.sys.get_nts(template_tree)
