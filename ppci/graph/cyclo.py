
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
    N = len(cfg.nodes)
    E = len(cfg.adj_map)
    P = 1  # For subroutines P = 1
    C = E - N + 2 * P
    return C


def connected_components(cfg):
    pass

