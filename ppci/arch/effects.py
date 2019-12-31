""" Effect descriptions.
"""


def Assign(lhs, rhs):
    return ("set", lhs, rhs)


def Set(lhs, rhs):
    return Assign(lhs, rhs)


PC = "pc"
