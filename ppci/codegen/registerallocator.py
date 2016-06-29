"""
Selected instructions use virtual registers and physical registers.
Register allocation is the process of assigning a register to the virtual
registers.

Some key concepts in the domain of register allocation are:

- **virtual register**: A value which must be mapped to a physical register.
- **physical register**: A real register
- **interference graph**: A graph in which each node represents a register.
  An edge indicates that the two registers cannot have the same register
  assigned.
- **pre-colored register**: A register that is already assigned a specific
  physical register.
- **coalescing**: The process of merging two nodes in an interference graph
  which do not interfere and are connected by a move instruction.
- **spilling**: Spilling is the process when no physical register can be found
  for a certain virtual register. Then this value will be placed in memory.
- **register class**: Most CPU's contain registers grouped into classes. For
  example, there may be registers for floating point, and registers for
  integer operations.
- **register alias**: Some registers may alias to registers in another class.
  A good example are the x86 registers rax, eax, ax, al and ah.

**Interference graph**

Each instruction in the instruction list may use or define certain registers.
A register is live between a use and define of a register. Registers that
are live at the same point in the program interfere with each other.
An interference graph is a graph in which each node represents a register
and each edge represents interference between those two registers.

**Graph coloring**

In 1981 Chaitin presented the idea to use graph coloring for register
allocation.

In a graph a node can be colored if it has less neighbours than
possible colors. This is true because when each neighbour has a different
color, there is still a valid color left for the node itself.

Given a graph, if a node can be colored, remove this node from the graph and
put it on a stack. When added back to the graph, it can be given a color.
Now repeat this process recursively with the remaining graph. When the
graph is empty, place all nodes back from the stack one by one and assign
each node a color when placed. Remember that when adding back, a color can
be found, because this was the criteria during removal.

See: https://en.wikipedia.org/wiki/Chaitin%27s_algorithm

**Coalescing**

**Spilling**

**Iterated register coalescing**

Iterated register coalescing (IRC) is a combination of graph coloring,
coalescing and spilling.
The process consists of the following steps:

- build an interference graph from the instruction list
- remove trivial colorable nodes.
- (optional) coalesc registers to remove redundant moves
- (optional) spill registers
- select registers

See: https://en.wikipedia.org/wiki/Register_allocation

**Graph coloring with more register classes**

Most instruction sets are not ideal, and hence simple graph coloring cannot
be used. The algorithm can be modified to work with several register
classes that possibly interfere.

[Runeson2003]_
[Smith2004]_


**Implementations**

The following class can be used to perform register allocation.

.. autoclass:: ppci.codegen.registerallocator.GraphColoringRegisterAllocator
    :members: alloc_frame, simplify, coalesc, freeze, is_colorable

"""

import logging
from functools import lru_cache
from collections import defaultdict
from .flowgraph import FlowGraph
from .interferencegraph import InterferenceGraph
from ..arch.arch import Architecture


# Nifty first function:
def first(x):
    """ Take the first element of a collection after sorting the things """
    x = list(x)
    # x.sort()
    return next(iter(x))


# TODO: implement linear scan allocator and other allocators!

class GraphColoringRegisterAllocator:
    """
        Target independent register allocator.
        Algorithm is iterated register coalescing by Appel and George.
        Also the pq-test algorithm for more register classes is added.
    """
    logger = logging.getLogger('regalloc')

    def __init__(self, arch: Architecture, debug_db):
        assert isinstance(arch, Architecture), arch
        self.arch = arch
        self.debug_db = debug_db

        # Register information:
        # TODO: Improve different register classes
        self.reg_colors = {}
        self.K = {}
        self.cls_regs = {}  # Mapping from 
        self.reg_alias = defaultdict(set)
        nmz = []
        for val in self.arch.register_classes:
            cls, _, kls, regs = val
            nmz.append((kls, cls))
            self.logger.debug('Register class "%s" contains %s', cls, regs)
            self.reg_colors[cls] = set(r.color for r in regs)
            self.K[cls] = len(regs)
            self.cls_regs[cls] = set(regs)
            for r in regs:
                self.reg_alias[r].add(r)  # The trivial alias: itself!
                for r2 in r.aliases:
                    self.reg_alias[r].add(r2)
                    self.reg_alias[r2].add(r)

        # TODO: Is this a hack?
        def cls_mapper(x):
            for c, n in nmz:
                if isinstance(x, c):
                    return n
            raise KeyError(x)

        self.cls_mapper = cls_mapper

    def alloc_frame(self, frame):
        """
            Do iterated register allocation for a single stack frame.
            This is the entry function for register allocator and drives
            through all stages.
        """
        self.init_data(frame)
        self.build()
        self.makeWorkList()
        self.logger.debug('Starting iterative coloring')
        while True:
            # self.check_invariants()

            # Run one of the possible steps:
            if self.simplifyWorklist:
                self.simplify()
            elif self.worklistMoves:
                self.coalesc()
            elif self.freeze_worklist:
                self.freeze()
            elif self.spillWorklist:  # pragma: no cover
                raise NotImplementedError('Spill not implemented')
            else:
                break   # Done!
        self.logger.debug('Now assinging colors')
        self.assign_colors()
        self.remove_redundant_moves()
        self.apply_colors()

    def init_data(self, frame):
        """ Initialize data structures """
        self.frame = frame

        # Move related sets:
        self.coalescedMoves = set()
        self.constrainedMoves = set()
        self.frozenMoves = set()
        self.activeMoves = set()
        self.worklistMoves = set()

    def build(self):
        """ 1. Construct interference graph from instruction list """
        self.frame.cfg = FlowGraph(self.frame.instructions)
        self.logger.debug(
            'Constructed flowgraph with %s nodes',
            len(self.frame.cfg.nodes))

        self.frame.cfg.calculate_liveness()
        self.frame.ig = InterferenceGraph(self.cls_mapper)
        self.frame.ig.calculate_interference(self.frame.cfg)
        self.logger.debug(
            'Constructed interferencegraph with %s nodes',
            len(self.frame.ig.nodes))

        # Divide nodes into pre-colored and initial:
        self.precolored = set(
            node for node in self.frame.ig.nodes if node.is_colored)
        self.initial = set(self.frame.ig.nodes - self.precolored)

        # Initialize color map:
        self.color = {}
        for node in self.precolored:
            self.logger.debug('Pre colored: %s', node)
            self.color[node] = node.color

        self.moves = [i for i in self.frame.instructions if i.ismove]
        for mv in self.moves:
            src = self.Node(mv.used_registers[0])
            dst = self.Node(mv.defined_registers[0])
            # assert src in self.initial | self.precolored
            # assert dst in self.initial | self.precolored, str(dst)
            src.moves.add(mv)
            dst.moves.add(mv)

    def makeWorkList(self):
        """ Divide initial nodes into worklists """
        self.select_stack = []

        # Fill initial move set, try to remove all moves:
        for m in self.moves:
            self.worklistMoves.add(m)

        # Make worklists for nodes:
        self.spillWorklist = []
        self.freeze_worklist = []
        self.simplifyWorklist = []

        while self.initial:
            node = self.initial.pop()
            self.logger.debug('Initial node: %s', node)
            if not self.is_colorable(node):
                self.spillWorklist.append(node)
            elif self.is_move_related(node):
                self.freeze_worklist.append(node)
            else:
                self.simplifyWorklist.append(node)

    def Node(self, vreg):
        return self.frame.ig.get_node(vreg)

    def has_edge(self, t, r):
        """ Helper function to check for an interfering edge """
        return self.frame.ig.has_edge(t, r)

    @lru_cache(maxsize=None)
    def q(self, B, C):
        """
        Determine the number of registers that can be blocked in
        class B by class C.
        """
        assert isinstance(B, str)
        assert isinstance(C, str)
        B_regs = self.cls_regs[B]
        C_regs = self.cls_regs[C]
        alias = self.reg_alias
        x = max(len(alias[r] & B_regs) for r in C_regs)
        self.logger.debug(
            'Class %s register can block max %s class %s register', C, x, B)
        return x

    def is_colorable(self, node):
        """
        Helper function to determine whether a node is trivially
        colorable. This means: no matter the colors of the nodes neighbours,
        the node can be given a color.

        In case of one register class, this is: n.degree < self.K

        In case of more than one register class, somehow the worst case
        damage by all neighbours must be determined.

        We do this now with the pq-test.
        """
        if node.is_colored:
            return True

        B = node.reg_class
        num_blocked = sum(self.q(B, j.reg_class) for j in node.adjecent)
        return num_blocked < self.K[B]

    def NodeMoves(self, n):
        return n.moves & (self.activeMoves | self.worklistMoves)

    def is_move_related(self, n):
        """ Check if a node is used by move instructions """
        return bool(self.NodeMoves(n))

    def simplify(self):
        """ Remove nodes from the graph """
        n = self.simplifyWorklist.pop()
        self.select_stack.append(n)
        self.logger.debug('Simplify node %s', n)

        # Pop out of graph, we place it back later:
        self.frame.ig.mask_node(n)
        for m in n.adjecent:
            self.decrement_degree(m)

    def decrement_degree(self, m):
        """ If a node was lowered in degree, check if there are nodes that
            can be moved from the spill list to the freeze of simplify
            list
        """
        # This check was m.degree == self.K - 1
        if m in self.spillWorklist and self.is_colorable(m):
            self.EnableMoves({m} | m.adjecent)
            self.spillWorklist.remove(m)
            if self.is_move_related(m):
                self.freeze_worklist.append(m)
            else:
                self.simplifyWorklist.append(m)

    def EnableMoves(self, nodes):
        for node in nodes:
            for m in self.NodeMoves(node):
                if m in self.activeMoves:
                    self.activeMoves.remove(m)
                    self.worklistMoves.add(m)

    def coalesc(self):
        """ Coalesc moves conservative.
            This means, merge the variables of a move into
            one variable, and delete the move. But do this
            only when no spill will occur.
        """
        # Remove the move from the worklist:
        m = self.worklistMoves.pop()
        x = self.Node(m.defined_registers[0])
        y = self.Node(m.used_registers[0])
        u, v = (y, x) if y in self.precolored else (x, y)
        self.logger.debug('Examining move %s which couples %s and %s', m, u, v)
        if u is v:
            # u is v, so we do 'mov x, x', which is redundant
            self.coalescedMoves.add(m)
            self.add_worklist(u)
            self.logger.debug('Move was mov x, x')
        elif v in self.precolored or self.has_edge(u, v):
            # Both u and v are precolored
            # or there is an interfering edge
            # between the two nodes:
            self.constrainedMoves.add(m)
            self.add_worklist(u)
            self.add_worklist(v)
            self.logger.debug('Move is constrained!')
        elif (u in self.precolored and
                all(self.Ok(t, u) for t in v.adjecent)) or \
                (u not in self.precolored and self.conservative(u, v)):
            # print('coalesce', 'u=',u, 'v=',v, 'vadj=',v.adjecent)
            self.logger.debug('Combining %s and %s', u, v)
            self.coalescedMoves.add(m)
            self.combine(u, v)
            self.add_worklist(u)
        else:
            self.logger.debug('Active move!')
            self.activeMoves.add(m)

    def add_worklist(self, u):
        if (u not in self.precolored) and (not self.is_move_related(u))\
                and self.is_colorable(u):
            self.freeze_worklist.remove(u)
            self.simplifyWorklist.append(u)

    def Ok(self, t, r):
        """ Implement coalescing testing with pre-colored register """
        # print('ok', t,r)
        return self.is_colorable(t) or \
            (t in self.precolored) or \
            self.has_edge(t, r)

    def conservative(self, u, v):
        """
            Briggs conservative criteria for coalescing:
            If the result of the merge has fewer than K nodes that are
            not trivially colorable, then coalescing is safe.
        """
        nodes = u.adjecent | v.adjecent
        k = len(list(filter(lambda n: not self.is_colorable(n), nodes)))
        # TODO: should this be altered for more register classes?
        return k < self.K[u.reg_class]

    def combine(self, u, v):
        """ Combine u and v into one node, updating work lists """
        # self.logger.debug('{} has degree {}'.format(v, v.degree))
        if v in self.freeze_worklist:
            self.freeze_worklist.remove(v)
        else:
            self.spillWorklist.remove(v)
        self.frame.ig.combine(u, v)

        # See if any adjecent nodes dropped in degree by merging u and v
        # This can happen when u and v both interfered with t.
        for t in u.adjecent:
            self.decrement_degree(t)

        # Move node to spill worklist if higher degree is reached:
        if (not self.is_colorable(u)) and u in self.freeze_worklist:
            self.freeze_worklist.remove(u)
            self.spillWorklist.append(u)

    def freeze(self):
        """ Give up coalescing on some node, move it to the simplify list
            and freeze all moves associated with it.
        """
        u = self.freeze_worklist.pop()
        self.logger.debug('freezing %s', u)
        self.simplifyWorklist.append(u)

        # Freeze moves for node u
        for m in self.NodeMoves(u):
            if m in self.activeMoves:
                self.activeMoves.remove(m)
            else:
                self.worklistMoves.remove(m)
            self.frozenMoves.add(m)
            # Check other part of the move for still being move related:
            src = self.Node(m.used_registers[0])
            dst = self.Node(m.defined_registers[0])
            v = src if u is dst else dst
            if v not in self.precolored and not self.is_move_related(v) \
                    and self.is_colorable(v):
                assert v in self.freeze_worklist
                self.freeze_worklist.remove(v)
                self.simplifyWorklist.append(v)

    def SelectSpill(self):  # pragma: no cover
        raise NotImplementedError("Spill is not implemented")

    def assign_colors(self):
        """ Add nodes back to the graph to color it. """
        while self.select_stack:
            node = self.select_stack.pop(-1)  # Start with the last added
            self.frame.ig.unmask_node(node)
            takenregs = set(self.color[m] for m in node.adjecent)
            ok_colors = self.reg_colors[node.reg_class] - takenregs
            if ok_colors:
                color = first(ok_colors)
                assert isinstance(color, int)
                self.logger.debug('Assign color %s to node %s', color, node)
                self.color[node] = color
                node.color = color
            else:  # pragma: no cover
                raise NotImplementedError('Spill required here!')

    def remove_redundant_moves(self):
        """ Remove coalesced moves """
        for move in self.coalescedMoves:
            self.frame.instructions.remove(move)

    def apply_colors(self):
        """ Assign colors to registers """
        # Apply all colors:
        for node in self.frame.ig:
            for reg in node.temps:
                if reg.is_colored:
                    assert reg.color == node.color
                else:
                    reg.set_color(node.color)
                # self.debug_db.map(reg, self.arch.get_register(node.color))

    def check_invariants(self):  # pragma: no cover
        """ Test invariants """
        # When changing the code, these asserts validate the worklists.
        assert all(self.is_colorable(u) for u in self.simplifyWorklist)
        assert all(not self.is_move_related(u) for u in self.simplifyWorklist)
        assert all(self.is_colorable(u) for u in self.freeze_worklist)
        assert all(self.is_move_related(u) for u in self.freeze_worklist)
        assert all(not self.is_colorable(u) for u in self.spillWorklist)

        # Check that moves live in exactly one set:
        assert self.activeMoves & self.worklistMoves & self.coalescedMoves \
            & self.constrainedMoves & self.frozenMoves == set()
