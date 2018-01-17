""" Rverse engineer the structured control flow of a program.

Possible algorithms:


References:

- relooper
  https://github.com/kripken/Relooper/blob/master/paper.pdf

[Cifuentes1998]_

[Baker1977]_


A hint might be "Hammock graphs" which are single entry, single exit graphs.
They might be the join point between dominator and post dominator nodes.

"""

import logging
from .utils.cfg import ir_function_to_graph, Loop


def find_structure(ir_function):
    """ Figure out the block structure of

    Args:
        ir_function: an `ir.SubRoutine` containing a soup-of-blocks.

    Returns:
        A control flow tree structure.
    """
    logger = logging.getLogger('structure-detection')
    logger.debug('finding structure for %s', ir_function)
    cfg, block_map = ir_function_to_graph(ir_function)
    sd = StructureDetector()
    shape = sd.detect(cfg)
    rmap = {c: b for b, c in block_map.items()}
    print()
    print_shape(shape)
    print()
    return shape, rmap


def print_shape(shape, indent=0):
    if isinstance(shape, BasicShape):
        print('   ' * indent + 'code:', str(shape.content))
    elif isinstance(shape, (BreakShape, ContinueShape)):
        print('   ' * indent + str(shape))
    elif isinstance(shape, SequenceShape):
        for sub_shape in shape.shapes:
            print_shape(sub_shape, indent=indent+1)
    elif isinstance(shape, IfShape):
        print('   ' * indent + 'if-then', shape.content)
        if shape.yes_shape is not None:
            print_shape(shape.yes_shape, indent=indent+1)

        if shape.no_shape is not None:
            print('   ' * indent + 'else')
            print_shape(shape.no_shape, indent=indent+1)
        print('   ' * indent + 'end-if')
    elif isinstance(shape, LoopShape):
        print('   ' * indent + 'loop')
        print_shape(shape.body, indent=indent+1)
        print('   ' * indent + 'end-loop')
    elif shape is None:
        pass
    else:
        raise NotImplementedError(str(shape))


class StructureDetector:
    logger = logging.getLogger('structure-detector')

    def detect(self, cfg):
        """ Find structure in control flow graph """
        self.cfg = cfg
        self.cfg.calculate_dominator_tree()

        # Loop info:
        self.loops = self.cfg.calculate_loops()
        self.loop_headers = {l.header: l for l in self.loops}

        self.marked = {self.cfg.exit_node}
        self.follow_stack = [self.cfg.exit_node]
        top_loop = Loop(
            header=self.cfg.entry_node,
            rest=(self.cfg.nodes - {self.cfg.entry_node}))

        # Stack of loops with follow nodes
        self.loop_stack = [(top_loop, None)]
        self.shapes = []
        shape = self.make_shape(self.cfg.entry_node)
        return shape

    def make_shape(self, entry):
        """ Given a set of blocks and an entry block, determine the shape """

        # Decide between loop, if-else or straight line code:
        if entry is self.cfg.exit_node:
            shape = None
        elif self.is_inactive_header(entry):
            # Loop found!
            loop = self.loop_headers[entry]
            follow_up = self.follows_loop(loop)
            assert follow_up
            self.loop_stack.append((loop, follow_up))
            self.marked.add(entry)
            self.marked.add(follow_up)

            self.logger.debug('--> Loop: %s break to %s', entry, follow_up)
            s1 = self.make_shape(entry)
            self.logger.debug('--> end loop')

            # Cleanup stacks:
            self.loop_stack.pop(-1)

            # Create shape:
            s2 = LoopShape(s1)
            s3 = self.make_shape(follow_up)
            shape = SequenceShape([s2, s3])
        elif len(entry.successors) == 1:
            # Simple straight ahead:
            self.logger.debug('--> code: %s', entry)
            follow_up, = entry.successors
            shape = BasicShape(entry)
            s2 = self.test(follow_up)
            if s2:
                shape = SequenceShape([shape, s2])
        elif len(entry.successors) == 2:
            # If statement!
            merger = self.cfg.get_immediate_post_dominator(entry)
            if merger in self.loop_stack[-1][0].rest:
                follow_up = merger
                self.marked.add(follow_up)
            else:
                follow_up = None
            yes, no = entry.yes, entry.no  # TODO: major hack for yes and no
            self.logger.debug('--> code %s', entry)
            self.logger.debug('--> if (based on) %s', entry)
            yes_shape = self.test(yes)
            self.logger.debug('--> else')
            no_shape = self.test(no)
            self.logger.debug('--> end if %s', entry)
            shape = IfShape(entry, yes_shape, no_shape)
            if follow_up:  # follow_up in same_loop:
                s2 = self.make_shape(follow_up)
                shape = SequenceShape([shape, s2])
        else:  # pragma: no cover
            raise NotImplementedError(str(entry))

        return shape

    def test(self, node):
        """ Check if a node is marked, or else shape it! """
        if node in self.marked:
            # Break or continue!
            if node is self.loop_stack[-1][0].header:
                return ContinueShape(0)
            elif node is self.loop_stack[-1][1]:
                return BreakShape(0)
            else:
                return None
        else:
            return self.make_shape(node)

    def is_inactive_header(self, block):
        if block in self.loop_headers:
            active_headers = {l[0].header for l in self.loop_stack}
            return block not in active_headers
        else:
            return False

    def follows_loop(self, loop):
        """ Determine the node that follows this loop """
        reachable_outside_loop = set()
        all_loop_nodes = [loop.header] + loop.rest
        for node in all_loop_nodes:
            for s in node.successors:
                if s not in all_loop_nodes:
                    reachable_outside_loop.add(s)

        if reachable_outside_loop:
            if len(reachable_outside_loop) != 1:
                reachables = ', '.join(map(str, reachable_outside_loop))
                raise ValueError(
                    'Loop followed by more then one node: {}'.format(
                        reachables))
            return list(reachable_outside_loop)[0]


class Relooper:
    """ Implementation of the relooper algorithm """
    # TODO: implement the relooper algorithm
    pass


class Shape:
    """ A control flow shape. """
    def __init__(self):
        pass


class BasicShape(Shape):
    def __init__(self, content):
        super().__init__()
        self.content = content


class BreakShape(Shape):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def __repr__(self):
        return 'Break-shape {}'.format(self.level)


class ContinueShape(Shape):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def __repr__(self):
        return 'Continue-shape {}'.format(self.level)


class SequenceShape(Shape):
    def __init__(self, shapes):
        super().__init__()
        self.shapes = shapes

    def __repr__(self):
        return 'Sequence of {}'.format(len(self.shapes))


class LoopShape(Shape):
    """ Loop shape """
    def __init__(self, body):
        super().__init__()
        self.body = body

    def __repr__(self):
        return 'Loop-shape'


class IfShape(Shape):
    """ If statement """
    def __init__(self, content, yes_shape, no_shape):
        super().__init__()
        self.content = content
        self.yes_shape = yes_shape
        self.no_shape = no_shape


class MultipleShape(Shape):
    """ Can be a switch statement? """
    pass
