import logging
from .flowgraph import FlowGraph
from .interferencegraph import InterferenceGraph

# Nifty first function:
def first(x):
    """ Take the first element of a collection after sorting the things """
    x = list(x)
    x.sort()
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
        self.logger.debug('Constructed flowgraph', extra={'ra_cfg':self.f.cfg})
        self.f.ig = InterferenceGraph(self.f.cfg)
        self.logger.debug('Constructed interferencegraph', extra={'ra_ig':self.f.ig})

        self.Node = self.f.ig.getNode

        # Divide nodes into pre-colored and initial:
        pre_tmp = list(self.f.tempMap.keys())
        self.precolored = set(self.Node(tmp) for tmp in pre_tmp)
        self.workSet = set(self.f.ig.nodes - self.precolored)

        for n in self.precolored:
            n.addDegree = 100 + len(self.f.ig.nodes) + self.K

        # Initialize color map:
        self.color = {}
        for tmp, c in self.f.tempMap.items():
            self.color[self.Node(tmp)] = c

        self.moves = [i for i in self.f.instructions if i.ismove]
        for mv in self.moves:
            self.Node(mv.src[0]).moves.add(mv)
            self.Node(mv.dst[0]).moves.add(mv)

    def NodeMoves(self, n):
        return n.moves & (self.activeMoves | self.worklistMoves)

    def MoveRelated(self, n):
        return bool(self.NodeMoves(n))

    @property
    def SpillWorkSet(self):
        c = lambda n: n.Degree >= self.K
        return set(filter(c, self.workSet))

    @property
    def FreezeWorkSet(self):
        c = lambda n: n.Degree < self.K and self.MoveRelated(n)
        return set(filter(c, self.workSet))

    @property
    def SimplifyWorkSet(self):
        c = lambda n: n.Degree < self.K and not self.MoveRelated(n)
        return set(filter(c, self.workSet))

    def makeWorkList(self):
        """ Divide initial nodes into worklists """
        self.selectStack = []

        # Fill initial move set:
        for m in self.moves:
            self.worklistMoves.add(m)

    def Simplify(self):
        """ 2. Remove nodes from the graph """
        n = first(self.SimplifyWorkSet)
        self.workSet.remove(n)
        self.selectStack.append(n)
        # Pop out of graph:
        self.f.ig.delNode(n)

    def EnableMoves(self, nodes):
        for n in nodes:
            for m in self.NodeMoves(n):
                if m in self.activeMoves:
                    self.activeMoves.remove(m)
                    self.worklistMoves.add(m)

    def Coalesc(self):
        """ Coalesc conservative. """
        m = first(self.worklistMoves)
        x = self.Node(m.dst[0])
        y = self.Node(m.src[0])
        u, v = (y, x) if y in self.precolored else (x, y)
        self.worklistMoves.remove(m)
        if u is v:
            self.coalescedMoves.add(m)
        elif v in self.precolored or self.f.ig.hasEdge(u, v):
            self.constrainedMoves.add(m)
        elif u not in self.precolored and self.Conservative(u, v):
            self.coalescedMoves.add(m)
            self.workSet.remove(v)
            self.f.ig.Combine(u, v)
        else:
            self.activeMoves.add(m)

    def Conservative(self, u, v):
        """ Briggs conservative criteria for coalesc """
        nodes = u.Adjecent | v.Adjecent
        c = lambda n: n.Degree >= self.K
        k = len(list(filter(c, nodes)))
        return k < self.K

    def Freeze(self):
        """ Give up coalescing on some node """
        u = first(self.FreezeWorkSet)
        self.freezeMoves(u)

    def freezeMoves(self, u):
        """ Freeze moves for node u """
        for m in self.NodeMoves(u):
            if m in self.activeMoves:
                self.activeMoves.remove(m)
            else:
                sekf.worklistMoves.remove(m)
            self.frozenMoves.add(m)
            # Check other part of the move for still being move related:
            v = m.src[0] if u is m.dst[0] else m.dst[0]

    def SelectSpill(self):
        raise NotImplementedError("Spill is not implemented")

    def AssignColors(self):
        """ Add nodes back to the graph to color it. """
        while self.selectStack:
            n = self.selectStack.pop(-1)  # Start with the last added
            self.f.ig.add_node(n)
            takenregs = set(self.color[m] for m in n.Adjecent)
            okColors = self.regs - takenregs
            if okColors:
                self.color[n] = first(okColors)
                n.color = self.color[n]
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

    def allocFrame(self, f):
        """ Do iterated register allocation for a single stack frame. """
        self.InitData(f)
        self.Build()
        self.makeWorkList()
        while True:
            if self.SimplifyWorkSet:
                self.Simplify()
            elif self.worklistMoves:
                self.Coalesc()
            elif self.FreezeWorkSet:
                self.Freeze()
            elif self.SpillWorkSet:
                raise NotImplementedError('Spill not implemented')
            else:
                break # Done!
        self.AssignColors()
        self.ApplyColors()
