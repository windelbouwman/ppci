
# Implementation of the relooper algorithm

class Relooper:
    pass


class Shape:
    def __init__(self, nxt):
        self.nxt = nxt


class Loop(Shape):
    """ Loop element """
    pass


class Multiple(Shape):
    """ Can be a if-else or switch """
    pass
