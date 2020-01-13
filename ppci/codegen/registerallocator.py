"""
Instructions generated during instruction selection phase use virtual
registers and some physical registers (e.g. when an instruction expects
arguments in particular register(s)). Register allocation is the process
of assigning physical location (register or memory) to the remaining
virtual registers.

Some key concepts in the domain of register allocation are:

- **virtual register**: A location which must be mapped to a physical register.
- **physical register**: A real CPU register
- **interference graph**: A graph in which each node represents a location.
  An edge indicates that the two locations cannot have the same physical
  register assigned.
- **pre-colored register**: A location that is already assigned a specific
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
A register is live between a definition and a use of that register. Registers that
are live at the same point in the program interfere with each other.
An interference graph is a graph in which each node represents a register
and each edge represents interference between those two registers.

**Graph coloring**

In 1981 Chaitin presented the idea to use graph coloring for register
allocation.

In a graph a node can be colored if it has less neighbours than
possible colors (referred to as K from now on). This is true because when
each neighbour has a different color, there is still a valid color left for
the node itself.

The outline of the algorithm is:
Given a graph, if a node can be colored, remove this node from the graph and
put it on a stack. When added back to the graph, it can be given a color.
Now repeat this process recursively with the remaining graph. When the
graph is empty, place all nodes back from the stack one by one and assign
each node a color when placed. Remember that when adding back, a color can
be found, because this was the criteria during removal.

See: https://en.wikipedia.org/wiki/Chaitin%27s_algorithm

[Chaitin1982]_

**Coalescing**

Coalescing is the process of merging two nodes in an interference graph.
This means that two temporaries will be assigned to the same register. This
is especially useful if the temporaries are used in move instructions, since
when the source and the destination of a move instruction are the same
register, the move can be deleted.

Coalescing a move instruction is easy when an interference graph is present.
Two nodes that are used by a move instruction can be coalesced when they do
not interfere.

However, if we coalesce too many moves, the graph can become uncolorable, and
spilling has to be done. To prevent spilling, coalescing must be done
in a controlled manner.

A conservative approach to the coalescing is the following: if the merged node has fewer than
K neighbours, then the nodes can be coalesced. The reason for
this is that when all nodes that can be colored are removed and the merged
node and its non-colored neighbours remain, the merged node can be colored.
This ensures that the coalescing of the nodes does not have a negative
effect on the colorability of the graph.

[Briggs1994]_

**Spilling**

**Iterated register coalescing**

Iterated register coalescing (IRC) is a combination of graph coloring,
coalescing and spilling.
The process consists of the following steps:

- build an interference graph from the instruction list
- remove trivial colorable nodes.
- (optional) coalesce registers to remove redundant moves
- (optional) spill registers
- select registers

See: https://en.wikipedia.org/wiki/Register_allocation

[George1996]_

**Graph coloring with more register classes**

Most instruction sets are not uniform, and hence simple graph coloring cannot
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
from ..arch.arch import Architecture, Frame
from ..arch.registers import Register
from ..utils.tree import Tree
from ..utils.collections import OrderedSet, OrderedDict
from .instructionselector import ContextInterface


class MiniCtx(ContextInterface):
    def __init__(self, frame, arch):
        self._frame = frame
        self._arch = arch
        self.l = []

    def move(self, dst, src):
        """ Generate move """
        self.emit(self._arch.move(dst, src))

    def emit(self, instruction):
        self.l.append(instruction)

    def new_reg(self, cls):
        return self._frame.new_reg(cls)


class MiniGen:
    """ Spill code generator """

    def __init__(self, arch, selector):
        self.arch = arch
        self.selector = selector

    def gen_load(self, frame, vreg, slot):
        """ Generate instructions to load vreg from a stack slot """
        at = self.make_at(slot)
        t = Tree(
            "MOVI{}".format(vreg.bitsize),
            Tree("LDRI{}".format(vreg.bitsize), at),
            value=vreg,
        )
        return self.gen(frame, t)

    def gen_store(self, frame, vreg, slot):
        """ Generate instructions to store vreg at a stack slot """
        at = self.make_at(slot)
        t = Tree(
            "STRI{}".format(vreg.bitsize),
            at,
            Tree("REGI{}".format(vreg.bitsize), value=vreg),
        )
        return self.gen(frame, t)

    def gen(self, frame, tree):
        """ Generate code for a given tree """
        ctx = MiniCtx(frame, self.arch)
        self.selector.gen_tree(ctx, tree)
        return ctx.l

    def make_at(self, slot):
        bitsize = self.arch.get_size("ptr") * 8
        offset_tree = Tree("FPRELU{}".format(bitsize), value=slot)
        # 'ADDI{}'.format(bitsize),
        #    Tree('REGI{}'.format(bitsize), value=self.arch.fp),
        #    Tree('CONSTI{}'.format(bitsize), value=offset))
        return offset_tree


def dfs_alias(r):
    """ Do a depth first search on the aliases member.

    This can be used to find aliases of aliases.
    """
    for r2 in r.aliases:
        for r3 in dfs_alias(r2):
            yield r3
        yield r2


# TODO: implement linear scan allocator and other allocators!


class GraphColoringRegisterAllocator:
    """ Target independent register allocator.

    Algorithm is iterated register coalescing by Appel and George.
    Also the pq-test algorithm for more register classes is added.
    """

    logger = logging.getLogger("regalloc")
    verbose = False  # Set verbose to True to get more logging info

    def __init__(self, arch: Architecture, instruction_selector):
        assert isinstance(arch, Architecture), arch
        self.arch = arch
        self.spill_gen = MiniGen(arch, instruction_selector)

        # Register information:
        # TODO: Improve different register classes
        self.K = {}  # type: Dict[Register, int]
        self.cls_regs = {}  # Mapping from class to register set
        self.alias = defaultdict(OrderedSet)
        for reg_class in self.arch.info.register_classes:
            kls, regs = reg_class.typ, reg_class.registers
            if self.verbose:
                self.logger.debug('Register class "%s" contains %s', kls, regs)

            self.K[kls] = len(regs)
            self.cls_regs[kls] = OrderedSet(regs)
            for r in regs:
                self.alias[r].add(r)  # The trivial alias: itself!
                for r2 in dfs_alias(r):
                    self.alias[r].add(r2)
                    self.alias[r2].add(r)

    def alloc_frame(self, frame: Frame):
        """ Do iterated register allocation for a single frame.

        This is the entry function for the register allocator and drives
        through all stages of the algorithm.

        Args:
            frame: The frame to perform register allocation on.
        """
        self.spill_rounds = 0
        self.init_data(frame)
        self.logger.debug("Starting iterative coloring")
        while True:
            # self.check_invariants()

            # Run one of the possible steps:
            if self.simplify_worklist:
                self.simplify()
            elif self.worklistMoves:
                self.coalesc()
            elif self.freeze_worklist:
                self.freeze()
            elif self.spill_worklist:
                self.spill()
                self.logger.debug("Starting over")
                self.init_data(frame)
            else:
                break  # Done!
        self.logger.debug("Now assinging colors")
        self.assign_colors()
        self.remove_redundant_moves()
        self.apply_colors()

    def link_move(self, move):
        """ Associate move with its source and destination """
        src = self.node(move.used_registers[0])
        dst = self.node(move.defined_registers[0])
        src.moves.add(move)
        dst.moves.add(move)

    def unlink_move(self, move):
        src = self.node(move.used_registers[0])
        dst = self.node(move.defined_registers[0])
        if move in src.moves:
            src.moves.remove(move)
        if move in dst.moves:
            dst.moves.remove(move)

    def init_data(self, frame):
        """ Initialize data structures """
        self.frame = frame

        cfg = FlowGraph(self.frame.instructions)
        self.logger.debug(
            "Constructed flowgraph with %s nodes", len(cfg.nodes)
        )

        cfg.calculate_liveness()
        self.frame.ig = InterferenceGraph()
        self.frame.ig.calculate_interference(cfg)
        self.logger.debug(
            "Constructed interferencegraph with %s nodes",
            len(self.frame.ig.nodes),
        )

        self.moves = [i for i in self.frame.instructions if i.ismove]
        for mv in self.moves:
            self.link_move(mv)

        self.select_stack = []

        # Move related sets:
        self.coalescedMoves = OrderedSet()
        self.constrainedMoves = OrderedSet()
        self.frozenMoves = OrderedSet()
        self.activeMoves = OrderedSet()
        self.worklistMoves = OrderedSet()

        # Fill initial move set, try to remove all moves:
        for m in self.moves:
            self.worklistMoves.add(m)

        # Make worklists for nodes:
        self.spill_worklist = OrderedSet()
        self.freeze_worklist = OrderedSet()
        self.simplify_worklist = OrderedSet()
        self.precolored = OrderedSet()

        # Divide nodes into categories:
        for node in self.frame.ig.nodes:
            if node.is_colored:
                if self.verbose:
                    self.logger.debug("Pre colored: %s", node)

                self.precolored.add(node)
            elif not self.is_colorable(node):
                self.spill_worklist.add(node)
            elif self.is_move_related(node):
                self.freeze_worklist.add(node)
            else:
                self.simplify_worklist.add(node)
        self.logger.debug(
            "%s node in spill list, %s in freeze list and %s in simplify list",
            len(self.spill_worklist),
            len(self.freeze_worklist),
            len(self.simplify_worklist),
        )

    def node(self, vreg):
        return self.frame.ig.get_node(vreg)

    def has_edge(self, t, r):
        """ Helper function to check for an interfering edge """
        if self.frame.ig.has_edge(t, r):
            return True

        if t in self.precolored:
            # Check aliases:
            for reg2 in self.alias[t.reg]:
                if self.frame.ig.has_node(reg2):
                    t2 = self.frame.ig.get_node(reg2, create=False)
                    if self.frame.ig.has_edge(t2, r):
                        return True

        if r in self.precolored:
            # Check aliases:
            for reg2 in self.alias[r.reg]:
                if self.frame.ig.has_node(reg2):
                    r2 = self.frame.ig.get_node(reg2, create=False)
                    if self.frame.ig.has_edge(t, r2):
                        return True

        return False

    @lru_cache(maxsize=None)
    def q(self, B, C):
        """ The number of class B registers that can be blocked by class C. """
        assert issubclass(B, Register)
        assert issubclass(C, Register)
        B_regs = self.cls_regs[B]
        C_regs = self.cls_regs[C]
        x = max(len(self.alias[r] & B_regs) for r in C_regs)
        if self.verbose:
            self.logger.debug(
                "Class %s register can block max %s class %s register", C, x, B
            )
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
        return n.moves

    def is_move_related(self, n):
        """ Check if a node is used by move instructions """
        return bool(self.NodeMoves(n))

    def simplify(self):
        """ Remove nodes from the graph """
        n = self.simplify_worklist.pop()
        self.select_stack.append(n)

        if self.verbose:
            self.logger.debug("Simplify node %s", n)

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
        if m in self.spill_worklist and self.is_colorable(m):
            self.enable_moves({m} | m.adjecent)
            self.spill_worklist.remove(m)
            if self.is_move_related(m):
                self.freeze_worklist.add(m)
            else:
                self.simplify_worklist.add(m)

    def enable_moves(self, nodes):
        for node in nodes:
            for move in self.NodeMoves(node):
                if move in self.activeMoves:
                    self.activeMoves.remove(move)
                    self.worklistMoves.add(move)

    def coalesc(self):
        """ Coalesc moves conservative.

        This means, merge the variables of a move into
        one variable, and delete the move. But do this
        only when no spill will occur.
        """
        # Remove the move from the worklist:
        m = self.worklistMoves.pop()
        x = self.node(m.defined_registers[0])
        y = self.node(m.used_registers[0])
        u, v = (y, x) if y in self.precolored else (x, y)
        if self.verbose:
            self.logger.debug("Coalescing %s which couples %s and %s", m, u, v)

        if u is v:
            # u is v, so we do 'mov x, x', which is redundant
            self.coalescedMoves.add(m)
            self.unlink_move(m)
            self.add_worklist(u)
            if self.verbose:
                self.logger.debug("Move was an identity move")
        elif (v in self.precolored) or self.has_edge(u, v):
            # Both u and v are precolored
            # or there is an interfering edge
            # between the two nodes:
            self.constrainedMoves.add(m)
            self.unlink_move(m)
            self.add_worklist(u)
            self.add_worklist(v)
            if self.verbose:
                self.logger.debug("Move is constrained!")
        elif (
            u.is_colored
            and issubclass(u.reg_class, v.reg_class)
            and all(self.ok(t, u) for t in v.adjecent)
        ) or ((not u.is_colored) and self.conservative(u, v)):
            # Check if v can be given the class of u, in other words:
            # is u a subclass of v?
            self.coalescedMoves.add(m)
            self.unlink_move(m)
            self.combine(u, v)
            self.add_worklist(u)
        else:
            self.logger.debug("Active move!")
            self.activeMoves.add(m)

    def add_worklist(self, u):
        if (
            (u not in self.precolored)
            and (not self.is_move_related(u))
            and self.is_colorable(u)
        ):
            self.freeze_worklist.remove(u)
            self.simplify_worklist.add(u)

    def ok(self, t, r):
        """ Implement coalescing testing with pre-colored register """
        return t.is_colored or self.is_colorable(t) or self.has_edge(t, r)

    def conservative(self, u, v):
        """ Briggs conservative criteria for coalescing.

        If the result of the merge has fewer than K nodes that are
        not trivially colorable, then coalescing is safe, because
        when coloring, all other nodes that can be colored will be popped
        from the graph, leaving the merged node that then can be colored.

        In the case of multiple register classes, first determine the
        new neighbour nodes. Then assume that all nodes that can be colored
        will be colored, and are taken out of the graph. Then calculate how
        many registers can be blocked by the remaining nodes. If this is
        less than the number of available registers, the coalesc is safe!
        """
        nodes = u.adjecent | v.adjecent
        B = self.common_reg_class(u.reg_class, v.reg_class)
        num_blocked = sum(
            self.q(B, j.reg_class) for j in nodes if not self.is_colorable(j)
        )
        return num_blocked < self.K[B]

    def combine(self, u, v):
        """ Combine u and v into one node, updating work lists """
        if self.verbose:
            self.logger.debug("Combining %s and %s", u, v)

        if v in self.freeze_worklist:
            self.freeze_worklist.remove(v)
        else:
            self.spill_worklist.remove(v)
        self.frame.ig.combine(u, v)
        u.reg_class = self.common_reg_class(u.reg_class, v.reg_class)

        if self.verbose:
            self.logger.debug("Combined node: %s", u)

        # See if any adjecent nodes dropped in degree by merging u and v
        # This can happen when u and v both interfered with t.
        for t in u.adjecent:
            self.decrement_degree(t)

        # Move node to spill worklist if higher degree is reached:
        if (not self.is_colorable(u)) and u in self.freeze_worklist:
            self.freeze_worklist.remove(u)
            self.spill_worklist.add(u)

    @lru_cache(maxsize=None)
    def common_reg_class(self, u, v):
        """ Determine the smallest common register class of two nodes """
        if issubclass(u, v):
            cc = u
        elif issubclass(v, u):
            cc = v
        else:
            raise RuntimeError(
                "Cannot determine common registerclass for {} and {}".format(
                    u, v
                )
            )

        if self.verbose:
            self.logger.debug("The common class of %s and %s is %s", u, v, cc)

        return cc

    def freeze(self):
        """ Give up coalescing on some node, move it to the simplify list
            and freeze all moves associated with it.
        """
        u = self.freeze_worklist.pop()
        if self.verbose:
            self.logger.debug("freezing %s", u)

        self.simplify_worklist.add(u)

        # Freeze moves for node u
        for m in list(self.NodeMoves(u)):
            if m in self.activeMoves:
                self.activeMoves.remove(m)
            else:
                self.worklistMoves.remove(m)
            self.unlink_move(m)
            self.frozenMoves.add(m)
            # Check other part of the move for still being move related:
            src = self.node(m.used_registers[0])
            dst = self.node(m.defined_registers[0])
            v = src if u is dst else dst
            if (
                v not in self.precolored
                and not self.is_move_related(v)
                and self.is_colorable(v)
            ):
                assert v in self.freeze_worklist
                self.freeze_worklist.remove(v)
                self.simplify_worklist.add(v)

    def spill(self):
        """ Do spilling """
        self.logger.debug("Spilling round %s", self.spill_rounds)
        self.spill_rounds += 1
        if self.spill_rounds > 30:
            raise RuntimeError("Give up: more than 10 spill rounds done!")
        # TODO: select a node which is certainly not a node that was
        # introduced during spilling?
        # Select to be spilled variable:
        # Select node with the lowest priority:
        p = []
        for n in self.spill_worklist:
            assert not n.is_colored
            d = sum(len(self.frame.ig.defs(t)) for t in n.temps)
            u = sum(len(self.frame.ig.uses(t)) for t in n.temps)
            priority = (u + d) / n.degree
            self.logger.debug("%s has spill priority=%s", n, priority)
            p.append((n, priority))
        node = min(p, key=lambda x: x[1])[0]
        # TODO: mark now, rewrite later?
        self.rewrite_program(node)

    def rewrite_program(self, node):
        """ Rewrite program by creating a load and a store for each use """
        # Generate spill code:
        self.logger.debug("Placing %s on stack", node)

        size = node.reg_class.bitsize // 8
        alignment = size
        slot = self.frame.alloc(size, alignment)
        self.logger.debug("Allocating stack slot %s", slot)
        # TODO: maybe break-up coalesced node before doing this?
        for tmp in node.temps:
            instructions = OrderedSet(
                self.frame.ig.uses(tmp) + self.frame.ig.defs(tmp)
            )
            for instruction in instructions:
                vreg2 = self.frame.new_reg(type(tmp))
                self.logger.debug("tmp: %s, new: %s", tmp, vreg2)
                instruction.replace_register(tmp, vreg2)
                if instruction.reads_register(vreg2):
                    code = self.spill_gen.gen_load(self.frame, vreg2, slot)
                    self.frame.insert_code_before(instruction, code)
                if instruction.writes_register(vreg2):
                    code = self.spill_gen.gen_store(self.frame, vreg2, slot)
                    self.frame.insert_code_after(instruction, code)

    def assign_colors(self):
        """ Add nodes back to the graph to color it. """
        while self.select_stack:
            node = self.select_stack.pop(-1)  # Start with the last added
            self.frame.ig.unmask_node(node)
            takenregs = set()
            for m in node.adjecent:
                for r in self.alias[m.reg]:
                    takenregs.add(r)
            ok_regs = self.cls_regs[node.reg_class] - takenregs
            assert ok_regs
            reg = ok_regs[0]

            if self.verbose:
                self.logger.debug("Assign %s to node %s", reg, node)

            node.reg = reg

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
                    assert reg.color == node.reg.color
                else:
                    reg.set_color(node.reg.color)

                # Mark the register as used in this frame:
                self.frame.used_regs.add(node.reg)
                # TODO:
                # if self.frame.debug_db:
                #    self.frame.debug_db.map(
                #        reg, self.arch.get_register(node.reg))

    def check_invariants(self):  # pragma: no cover
        """ Test invariants """
        # When changing the code, these asserts validate the worklists.
        assert all(self.is_colorable(u) for u in self.simplify_worklist)
        assert all(not self.is_move_related(u) for u in self.simplify_worklist)
        assert all(self.is_colorable(u) for u in self.freeze_worklist)
        assert all(self.is_move_related(u) for u in self.freeze_worklist)
        assert all(not self.is_colorable(u) for u in self.spill_worklist)

        # Check that moves live in exactly one set:
        assert (
            self.activeMoves
            & self.worklistMoves
            & self.coalescedMoves
            & self.constrainedMoves
            & self.frozenMoves
            == set()
        )
