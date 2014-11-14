import logging
from .flowgraph import FlowGraph
from .interferencegraph import InterferenceGraph


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

    """
    def __init__(self):
        self.logger = logging.getLogger('registerallocator')

    def InitData(self, f):
        self.f = f
        # Register information:
        self.regs = set(f.regs)
        self.K = len(self.regs)

        # Move related sets:
        self.coalescedMoves = set()
        self.constrainedMoves = set()
        self.frozenMoves = set()
        self.activeMoves = set()
        self.worklistMoves = set()

    def Build(self):
        """ 1. Construct interference graph from instruction list """
        self.f.cfg = FlowGraph(self.f.instructions)
        self.logger.debug('Constructed flowgraph with {} nodes'
                          .format(len(self.f.cfg.nodes)))

        self.f.cfg.calculate_liveness()
        self.f.ig = InterferenceGraph(self.f.cfg)
        self.logger.debug('Constructed interferencegraph with {} nodes'
                          .format(len(self.f.ig.nodes)))

        self.Node = self.f.ig.get_node

        # Divide nodes into pre-colored and initial:
        pre_tmp = list(self.f.tempMap.keys())
        self.precolored = set(self.Node(tmp) for tmp in pre_tmp)
        self.initial = set(self.f.ig.nodes - self.precolored)

        # TODO: do not add the pre colored nodes at all.
        for n in self.precolored:
            # give pre colored nodes infinite degree:
            n.addDegree = 100 + len(self.f.ig.nodes) + self.K

        # Initialize color map:
        self.color = {}
        for tmp, color in self.f.tempMap.items():
            self.color[self.Node(tmp)] = color

        self.moves = [i for i in self.f.instructions if i.ismove]
        for mv in self.moves:
            src = self.Node(mv.src[0])
            dst = self.Node(mv.dst[0])
            # assert src in self.initial | self.precolored
            # assert dst in self.initial | self.precolored, str(dst)
            src.moves.add(mv)
            dst.moves.add(mv)

    def makeWorkList(self):
        """ Divide initial nodes into worklists """
        self.selectStack = []

        # Fill initial move set:
        for m in self.moves:
            self.worklistMoves.add(m)

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
        return bool(self.NodeMoves(n))

    def Simplify(self):
        """ 2. Remove nodes from the graph """
        n = self.simplifyWorklist.pop()
        # self.logger.debug('Simplifying the graph, taking out {}'.format(n))
        self.selectStack.append(n)
        # Pop out of graph, we place it back later:
        self.f.ig.mask_node(n)
        for m in n.Adjecent:
            self.decrement_degree(m)

    def decrement_degree(self, m):
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
        """ Coalesc moves conservative.
            This means, merge the variables of a move into
            one variable, and delete the move. But do this
            only when no spill will occur.
        """
        m = first(self.worklistMoves)
        x = self.Node(m.dst[0])
        y = self.Node(m.src[0])
        # self.logger.debug('Coalescing {} and {}'.format(x, y))
        u, v = (y, x) if y in self.precolored else (x, y)
        self.worklistMoves.remove(m)
        if u is v:
            self.logger.debug('u == v')
            self.coalescedMoves.add(m)
            self.add_worklist(u)
        elif v in self.precolored or self.f.ig.has_edge(u, v):
            # self.logger.debug('Constrained')
            self.constrainedMoves.add(m)
            self.add_worklist(u)
            self.add_worklist(v)
        elif (u in self.precolored and all(self.Ok(t, u) for t in v.Adjecent)) or \
                (u not in self.precolored and self.Conservative(u, v)):
            # self.logger.debug('Combining {} and {}'.format(u, v))
            self.coalescedMoves.add(m)
            self.Combine(u, v)
            self.add_worklist(u)
        else:
            # self.logger.debug('Active move?')
            self.activeMoves.add(m)

    def add_worklist(self, u):
        if u not in self.precolored and not self.MoveRelated(u)\
                and u.Degree < self.K:
            self.freezeWorklist.remove(u)
            self.simplifyWorklist.append(u)

    def Ok(self, t, r):
        """ Implement coalescing testing with pre-colored register """
        return t.Degree < self.K or \
            t in self.precolored or \
            self.f.ig.has_edge(t, r)

    def Conservative(self, u, v):
        """ Briggs conservative criteria for coalesc """
        nodes = u.Adjecent | v.Adjecent
        c = lambda n: n.Degree >= self.K
        k = len(list(filter(c, nodes)))
        return k < self.K

    def Combine(self, u, v):
        """ Combine u and v into one node, updating work lists """
        # self.logger.debug('{} has degree {}'.format(v, v.Degree))
        if v in self.freezeWorklist:
            self.freezeWorklist.remove(v)
        else:
            self.spillWorklist.remove(v)
        self.f.ig.combine(u, v)

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
            src, dst = self.Node(m.src[0]), self.Node(m.dst[0])
            v = src if u is dst else dst
            if v not in self.precolored and not self.MoveRelated(v) \
                    and v.Degree < self.K:
                assert v in self.freezeWorklist, \
                    '{} not in freezeworklist'.format(v)
                self.freezeWorklist.remove(v)
                self.simplifyWorklist.append(v)

    def SelectSpill(self):
        raise NotImplementedError("Spill is not implemented")

    def AssignColors(self):
        """ Add nodes back to the graph to color it. """
        while self.selectStack:
            node = self.selectStack.pop(-1)  # Start with the last added
            self.f.ig.unmask_node(node)
            takenregs = set(self.color[m] for m in node.Adjecent)
            okColors = self.regs - takenregs
            if okColors:
                self.color[node] = first(okColors)
                node.color = self.color[node]
            else:
                raise NotImplementedError('Spill required here!')

    def ApplyColors(self):
        # Remove coalesced moves:
        for mv in self.coalescedMoves:
            self.f.instructions.remove(mv)

        # Use allocated registers:
        lookup = lambda t: self.color[self.Node(t)]
        for i in self.f.instructions:
            i.src = tuple(map(lookup, i.src))
            i.dst = tuple(map(lookup, i.dst))

    def check_invariants(self):
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

    def allocFrame(self, f):
        """ Do iterated register allocation for a single stack frame. """
        self.InitData(f)
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
            elif self.spillWorklist:
                raise NotImplementedError('Spill not implemented')
            else:
                break   # Done!
        self.logger.debug('Now assinging colors')
        self.AssignColors()
        self.ApplyColors()
