from .. import ir


def make(function, frame):
    """
        Create canonicalized version of the IR-code. This means:
        - Calls out of expressions.
        - Other things?
    """
    # Change the tree. This modifies the IR-tree!
    # Move all parameters into registers
    parmoves = []
    for p in function.arguments:
        pt = newTemp()
        frame.parMap[p] = pt
        parmoves.append(ir.Move(pt, frame.argLoc(p.num)))
    function.entry.instructions = parmoves + function.entry.instructions

    # TODO: schedule here?

