import logging
from .flowgraph import FlowGraph
from .interferencegraph import InterferenceGraph
from ..arch.arch import Architecture


# Nifty first function:
def first(x):
    """ Take the first element of a collection after sorting the things """
    x = list(x)
    # x.sort()
    return next(iter(x))


class RegisterAllocator:
    """
        Target independent register allocator.

        Algorithm is iterated register coalescing by Appel and George.

        Chaitin's algorithm: remove all nodes with less than K neighbours.
        These nodes can be colored when added back.

        The process consists of the following steps:

        - build interference graph from the instruction list
        - remove low degree non move related nodes.
        - (optional) coalesc registers to remove redundant moves
        - (optional) spill registers
        - select registers

        TODO: Implement different register classes
    """
    logger = logging.getLogger('registerallocator')

    def __init__(self, arch, debug_db):
        assert isinstance(arch, Architecture), arch
        self.arch = arch
        self.debug_db = debug_db

    def init_data(self, frame):
        """ Initialize data structures """
        self.frame = frame

        # Register information:
        self.reg_colors = set(reg.color for reg in frame.regs)
        self.K = len(self.reg_colors)

        # Move related sets:
        self.coalescedMoves = set()
        self.constrainedMoves = set()
        self.frozenMoves = set()
        self.activeMoves = set()
        self.worklistMoves = set()

    def Build(self):
        """ 1. Construct interference graph from instruction list """
        self.frame.cfg = FlowGraph(self.frame.instructions)
        self.logger.debug('Constructed flowgraph with {} nodes'
                          .format(len(self.frame.cfg.nodes)))

        self.frame.cfg.calculate_liveness()
        self.frame.ig = InterferenceGraph(self.frame.cfg)
        self.logger.debug('Constructed interferencegraph with {} nodes'
                          .format(len(self.frame.ig.nodes)))

        # Divide nodes into pre-colored and initial:
        self.precolored = set(
            node for node in self.frame.ig.nodes if node.color is not None)
        self.initial = set(self.frame.ig.nodes - self.precolored)

        # TODO: do not add the pre colored nodes at all.
        for n in self.precolored:
            # give pre colored nodes infinite degree:
            n.addDegree = 100 + len(self.frame.ig.nodes) + self.K

        # Initialize color map:
        self.color = {}
        for node in self.precolored:
            self.color[node] = node.color

        self.moves = [i for i in self.frame.instructions if i.ismove]
        for mv in self.moves:
            src = self.Node(mv.used_registers[0])
            dst = self.Node(mv.defined_registers[0])
            # assert src in self.initial | self.precolored
            # assert dst in self.initial | self.precolored, str(dst)
            src.moves.add(mv)
            dst.moves.add(mv)

    def Node(self, vreg):
        return self.frame.ig.get_node(vreg)

    def has_edge(self, t, r):
        """ Helper function to check for an interfering edge """
        return self.frame.ig.has_edge(t, r)

    def makeWorkList(self):
        """ Divide initial nodes into worklists """
        self.selectStack = []

        # Fill initial move set, try to remove all moves:
        for m in self.moves:
            self.worklistMoves.add(m)

        # Make worklists for nodes:
        self.spillWorklist = []
        self.freezeWorklist = []
        self.simplifyWorklist = []

        while self.initial:
            n = self.initial.pop()
            if n.Degree >= self.K:
                self.spillWorklist.append(n)
            elif self.MoveRelated(n):
                self.freezeWorklist.append(n)
            else:
                self.simplifyWorklist.append(n)

    def NodeMoves(self, n):
        return n.moves & (self.activeMoves | self.worklistMoves)

    def MoveRelated(self, n):
        """ Check if a node is used by move instructions """
        return bool(self.NodeMoves(n))

    def Simplify(self):
        """ 2. Remove nodes from the graph """
        n = self.simplifyWorklist.pop()
        self.selectStack.append(n)
        # Pop out of graph, we place it back later:
        self.frame.ig.mask_node(n)
        for m in n.Adjecent:
            self.decrement_degree(m)

    def decrement_degree(self, m):
        """ If a node was lowered in degree, check if there are nodes that
            can be moved from the spill list to the freeze of simplify
            list
        """
        if m.Degree == self.K - 1 and m in self.spillWorklist:
            self.EnableMoves({m} | m.Adjecent)
            self.spillWorklist.remove(m)
            if self.MoveRelated(m):
                self.freezeWorklist.append(m)
            else:
                self.simplifyWorklist.append(m)

    def EnableMoves(self, nodes):
        for node in nodes:
            for m in self.NodeMoves(node):
                if m in self.activeMoves:
                    self.activeMoves.remove(m)
                    self.worklistMoves.add(m)

    def Coalesc(self):
        """ 3. Coalesc moves conservative.
            This means, merge the variables of a move into
            one variable, and delete the move. But do this
            only when no spill will occur.
        """
        # Remove the move from the worklist:
        m = self.worklistMoves.pop()
        x = self.Node(m.defined_registers[0])
        y = self.Node(m.used_registers[0])
        u, v = (y, x) if y in self.precolored else (x, y)
        # print('u,v', u, v)
        if u is v:
            # u is v, so we do 'mov x, x', which is redundant
            self.coalescedMoves.add(m)
            self.add_worklist(u)
        elif v in self.precolored or self.has_edge(u, v):
            # Both u and v are precolored
            # or there is an interfering edge
            # between the two nodes:
            self.constrainedMoves.add(m)
            self.add_worklist(u)
            self.add_worklist(v)
        elif (u in self.precolored and
                all(self.Ok(t, u) for t in v.Adjecent)) or \
                (u not in self.precolored and self.conservative(u, v)):
            # print('coalesce', 'u=',u, 'v=',v, 'vadj=',v.Adjecent)
            self.coalescedMoves.add(m)
            self.combine(u, v)
            self.add_worklist(u)
        else:
            self.activeMoves.add(m)

    def add_worklist(self, u):
        if (u not in self.precolored) and (not self.MoveRelated(u))\
                and (u.Degree < self.K):
            self.freezeWorklist.remove(u)
            self.simplifyWorklist.append(u)

    def Ok(self, t, r):
        """ Implement coalescing testing with pre-colored register """
        # print('ok', t,r)
        return (t.Degree < self.K) or \
            (t in self.precolored) or \
            self.has_edge(t, r)

    def conservative(self, u, v):
        """ Briggs conservative criteria for coalesc """
        nodes = u.Adjecent | v.Adjecent
        k = len(list(filter(lambda n: n.Degree >= self.K, nodes)))
        return k < self.K

    def combine(self, u, v):
        """ Combine u and v into one node, updating work lists """
        # self.logger.debug('{} has degree {}'.format(v, v.Degree))
        if v in self.freezeWorklist:
            self.freezeWorklist.remove(v)
        else:
            self.spillWorklist.remove(v)
        self.frame.ig.combine(u, v)

        # See if any adjecent nodes dropped in degree by merging u and v
        # This can happen when u and v both interfered with t.
        for t in u.Adjecent:
            self.decrement_degree(t)

        # Move node to spill worklist if higher degree is reached:
        if u.Degree >= self.K and u in self.freezeWorklist:
            self.freezeWorklist.remove(u)
            self.spillWorklist.append(u)

    def Freeze(self):
        """ Give up coalescing on some node, move it to the simplify list
            and freeze all moves associated with it.
        """
        print('freeze')
        u = self.freezeWorklist.pop()
        self.simplifyWorklist.append(u)
        self.freezeMoves(u)

    def freezeMoves(self, u):
        """ Freeze moves for node u """
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
            if v not in self.precolored and not self.MoveRelated(v) \
                    and v.Degree < self.K:
                assert v in self.freezeWorklist, \
                    '{} not in freezeworklist'.format(v)
                self.freezeWorklist.remove(v)
                self.simplifyWorklist.append(v)

    def SelectSpill(self):  # pragma: no cover
        raise NotImplementedError("Spill is not implemented")

    def assign_colors(self):
        """ Add nodes back to the graph to color it. """
        while self.selectStack:
            node = self.selectStack.pop(-1)  # Start with the last added
            self.frame.ig.unmask_node(node)
            takenregs = set(self.color[m] for m in node.Adjecent)
            okColors = self.reg_colors - takenregs
            if okColors:
                self.color[node] = first(okColors)
                node.color = self.color[node]
                assert type(node.color) is int
            else:  # pragma: no cover
                raise NotImplementedError('Spill required here!')

    def remove_redundant_moves(self):
        # Remove coalesced moves:
        for mv in self.coalescedMoves:
            self.frame.instructions.remove(mv)

    def ApplyColors(self):
        """ Assign colors to registers """
        # Apply all colors:
        for node in self.frame.ig:
            for reg in node.temps:
                if reg.is_colored:
                    assert reg.color == node.color
                else:
                    reg.set_color(node.color)
                self.debug_db.map(reg, self.arch.get_register(node.color))

    def check_invariants(self):  # pragma: no cover
        """ Test invariants """
        # When changing the code, these asserts validate the worklists.
        assert all(u.Degree < self.K for u in self.simplifyWorklist)
        assert all(not self.MoveRelated(u) for u in self.simplifyWorklist)
        assert all(u.Degree < self.K for u in self.freezeWorklist)
        assert all(self.MoveRelated(u) for u in self.freezeWorklist)
        assert all(u.Degree >= self.K for u in self.spillWorklist)

        # Check that moves live in exactly one set:
        assert self.activeMoves & self.worklistMoves & self.coalescedMoves \
            & self.constrainedMoves & self.frozenMoves == set()

    def alloc_frame(self, frame):
        """ Do iterated register allocation for a single stack frame. """
        self.init_data(frame)
        self.Build()
        self.makeWorkList()
        self.logger.debug('Starting iterative coloring')
        while True:
            # self.check_invariants()

            # Run one of the possible steps:
            if self.simplifyWorklist:
                self.Simplify()
            elif self.worklistMoves:
                self.Coalesc()
            elif self.freezeWorklist:
                self.Freeze()
            elif self.spillWorklist:  # pragma: no cover
                raise NotImplementedError('Spill not implemented')
            else:
                break   # Done!
        self.logger.debug('Now assinging colors')
        self.assign_colors()
        self.remove_redundant_moves()
        self.ApplyColors()
