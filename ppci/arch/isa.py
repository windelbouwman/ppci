"""
Isa related classes.
These can be used to define an instruction set.
"""

from collections import namedtuple
from ..utils.tree import Tree, from_string


Pattern = namedtuple(
    'Pattern',
    ['non_term', 'tree', 'size', 'cycles', 'energy', 'condition', 'method'])


class Isa:
    """
        Container type for an instruction set.
        Contains a list of instructions, mappings from intermediate code
        to instructions.

        Isa's can be merged into new isa's which can be used to define target.
        For example the arm without FPU can be combined with the FPU isa
        to expand the supported functions.
    """
    def __init__(self):
        self.instructions = []
        self.relocation_map = {}
        self.patterns = []
        self.peepholes = []

    def __add__(self, other):
        assert isinstance(other, Isa)
        isa3 = Isa()
        isa3.instructions = self.instructions + other.instructions
        isa3.patterns = self.patterns + other.patterns
        isa3.relocation_map = self.relocation_map.copy()
        isa3.relocation_map.update(other.relocation_map)
        return isa3

    def add_instruction(self, i):
        """ Register an instruction into this ISA """
        self.instructions.append(i)

    def register_relocation(self, relocation):
        """ Register a relocation into this isa """
        name = relocation.__name__
        self.relocation_map[name] = relocation
        return relocation

    def register_pattern(self, pattern):
        """ Add a pattern to this isa """
        self.patterns.append(pattern)

    def peephole(self, function):
        """ Add a peephole optimization function """
        self.peepholes.append(function)
        return function

    def pattern(
            self, non_term, tree, condition=None,
            size=1, cycles=1, energy=1):
        """
            Decorator function that adds a pattern.
        """
        if isinstance(tree, str):
            tree = from_string(tree)

        assert isinstance(tree, Tree)
        assert isinstance(size, int)

        def wrapper(function):
            """ Wrapper that add the function with the paramaters """
            pat = Pattern(
                non_term, tree, size, cycles, energy, condition, function)
            self.register_pattern(pat)
            return function
        return wrapper


class Relocation:
    """
        Contains information on the relocation to apply.
    """
    def __init__(self, label_prop, reloc_function):
        self.a = label_prop
        self.reloc_function = reloc_function
