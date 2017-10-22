"""
Functions related to inspecting Program objects/classes in a graph.
"""

from .base import Program, get_program_classes


def get_targets(program):
    """ Get the program names that the given Program instance/subclass
    can be compiled to.
    """
    subclasses = get_program_classes()
    cls = program
    if not isinstance(program, type):
        cls = type(program)
    if not issubclass(cls, Program):
        raise TypeError('get_targets() needs Program instance or class.')
    
    targets = set()
    for method_name in dir(cls):
        if method_name.startswith('to_') and callable(getattr(cls, method_name)):
            prog_name = method_name[3:]
            if prog_name in subclasses:
                targets.add(prog_name)
    return targets


def create_program_graph():
    """ Produce a networkx graph where the nodes are language names and the
    (directed) edges represent compilers.
    """
    import networkx as nx
    IGNORE = '', 'sourcecode', 'intermediate', 'machine'
    subclasses = get_program_classes()
    
    g = nx.DiGraph()
    for name in subclasses.keys():
        if not name in IGNORE:
            g.add_node(name)
    for name, programClass in subclasses.items():
        for target in get_targets(programClass):
            g.add_edge(name, target)
    return g


def mcp(program, target_name):
    """ Find the chain of representations to go from the given Program instance
    to the target language. Returns None if no path was found.
    
    This is essentially the Minimum Cost Path algorithm, and we can
    improve this to weight costs in various ways.
    """
    subclasses = get_program_classes()
    
    # Init front list of (cost, program1, program2, ...)
    front = [(1, program.language, tgt) for tgt in get_targets(program)]
    chains = []  # valid chains, sorted by length
    visited = set()
    visited.add(program.language)
    
    while True:
        
        # Are any chains finished?
        for i in reversed(range(len(front))):
            chain = front[i]
            if chain[-1] == target_name:
                chains.append(chain[1:])  # skip costs
                front.pop(i)
        
        # Are we finished?
        if not front:
            break
        
        # Expand front to target of each node in the front
        new_visited = set()
        
        for i in reversed(range(len(front))):
            chain = front.pop(i)
            program = subclasses[chain[-1]]
            for tgt in get_targets(program):  # For each target
                if tgt not in visited:
                    new_chain = (chain[0] +1, ) + chain[1:] + (tgt, )
                    front.append(new_chain)
                    new_visited.add(tgt)
        visited.update(new_visited)
        if not new_visited:
            break
    
    return chains
