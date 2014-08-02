""" Create a tree from ir code.
    For example, some sequence like this:
    const1 = 2
    const2 = 12
    add1 = p0 + const1
    mul2 = add1 * const2

    will become:
    MULI32(ADDI32(p0, CONST(2)), CONST(12))
"""



