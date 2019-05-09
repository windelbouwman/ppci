""" Calculate the cyclomatic complexity.

Cyclomatic complexity is defined as:

C = E - N + 2 * P

Where:
E = number of edges
N = number of nodes
P = number of connected components.

For functions and procedures P = 1.

So the formula for a single subroutine is:

C = E - N + 2

"""


def cyclomatic_complexity(cfg):
    """ Determine the cyclomatic complexity of a CFG (control-flow-graph) """
    N = len(cfg.nodes)
    E = cfg.get_number_of_edges()
    P = 1  # For subroutines P = 1
    C = E - N + 2 * P
    return C


def connected_components(cfg):
    # TODO: implement this graph logic when required.
    pass
