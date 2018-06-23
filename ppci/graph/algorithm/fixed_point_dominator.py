
def calculate_dominators(nodes, entry_node):
    """ Calculate the dominator sets iteratively """

    # Initialize dominator map:
    _dom = {}
    for node in nodes:
        if node is entry_node:
            _dom[node] = {node}
        else:
            _dom[node] = set(nodes)

    # Run fixed point iteration:
    change = True
    while change:
        change = False
        for node in nodes:
            # A node is dominated by itself and by the intersection of
            # the dominators of its predecessors
            pred_doms = list(
                _dom[p] for p in node.predecessors)
            if pred_doms:
                new_dom_n = set.union({node}, set.intersection(*pred_doms))
                if new_dom_n != _dom[node]:
                    change = True
                    _dom[node] = new_dom_n
    return _dom


def calculate_post_dominators(nodes, exit_node):
    """ Calculate the post dominator sets iteratively.

    Post domination is the same as domination, but then starting at
    the exit node.
    """

    # Initialize dominator map:
    _pdom = {}
    for node in nodes:
        if node is exit_node:
            _pdom[node] = {node}
        else:
            _pdom[node] = set(nodes)

    # Run fixed point iteration:
    change = True
    while change:
        change = False
        for node in nodes:
            # A node is post dominated by itself and by the intersection
            # of the post dominators of its successors
            succ_pdoms = list(
                _pdom[s] for s in node.successors)
            if succ_pdoms:
                new_pdom_n = set.union(
                    {node}, set.intersection(*succ_pdoms))
                if new_pdom_n != _pdom[node]:
                    change = True
                    _pdom[node] = new_pdom_n

    return _pdom


def calculate_immediate_dominators(nodes, _dom, _sdom):
    """ Determine immediate dominators from dominators and strict dominators.
    """

    _idom = {}

    for node in nodes:
        if _sdom[node]:
            for x in _sdom[node]:
                if _dom[x] == _sdom[node]:
                    # This must be the only definition of idom:
                    assert node not in _idom
                    _idom[node] = x
        else:
            # No strict dominators, hence also no immediate dominator:
            _idom[node] = None
    return _idom


def calculate_immediate_post_dominators(nodes, _pdom, _spdom):
    """ Calculate immediate post dominators for all nodes.

    Do this by choosing n from spdom(x) such that pdom(n) == spdom(x).
    """

    _ipdom = {}

    for node in nodes:
        if _spdom[node]:
            for x in _spdom[node]:
                if _pdom[x] == _spdom[node]:
                    # This must be the only definition of ipdom:
                    assert node not in _ipdom
                    _ipdom[node] = x
        else:
            # No strict post dominators, hence also no
            # immediate post dominator:
            _ipdom[node] = None
    return _ipdom
