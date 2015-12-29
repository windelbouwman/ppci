class State:
    """ State used to label tree nodes """
    def __init__(self):
        self.labels = {}

    def has_goal(self, goal):
        return goal in self.labels

    def get_cost(self, goal):
        return self.labels[goal][0]

    def get_rule(self, goal):
        return self.labels[goal][1]

    def set_cost(self, goal, cost, rule):
        """
            Mark that this tree can be matched with a rule for a certain cost
        """
        if self.has_goal(goal):
            if self.get_cost(goal) > cost:
                self.labels[goal] = (cost, rule)
        else:
            self.labels[goal] = (cost, rule)


class BaseMatcher:
    """ Base class for matcher objects. """
    def kids(self, tree, rule):
        return self.kid_functions[rule](tree)

    def nts(self, rule):
        return self.nts_map[rule]

    def burm_label(self, tree):
        """ Label all nodes in the tree bottom up """
        for c in tree.children:
            self.burm_label(c)
        self.burm_state(tree)

    def apply_rules(self, tree, goal):
        rule = tree.state.get_rule(goal)
        results = [self.apply_rules(kid_tree, kid_goal)
                   for kid_tree, kid_goal in
                   zip(self.kids(tree, rule), self.nts(rule))]
        return self.pat_f[rule](tree, *results)
