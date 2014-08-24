
# Valid tree names:
tree_names = ['ADDI32', 'SUBI32', 'MULI32', 'ADR',
    'ORI32', 'SHLI32', 'SHRI32', 'ANDI32',
'CONSTI32 CONSTDATA MEMI32 REGI32', 'CALL GLOBALADDRESS',
'MOVI32']


class Tree:
    """ Tree node with a name and possibly some child nodes """
    def __init__(self, name, *args, value=None):
        self.name = name
        self.value = value
        self.children = args

    def __repr__(self):
        if self.children:
            ch = ', '.join(str(c) for c in self.children)
            ch = '({})'.format(ch)
        else:
            ch = ''
        if self.value is not None:
            val = '[{}]'.format(self.value)
        else:
            val = ''
        return '{}{}{}'.format(self.name, val, ch)


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
                   for kid_tree, kid_goal in zip(self.kids(tree, rule), self.nts(rule))]
        return self.pat_f[rule](tree, *results)
