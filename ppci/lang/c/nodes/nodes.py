""" Classes for the abstract syntax tree (AST) nodes for the C language.

The goal is to be able to recreate source from this ast as close to
the original source as possible.
"""

# pylint: disable=R0903


class CompilationUnit:
    """ A single compilation unit """

    def __init__(self, declarations):
        self.declarations = declarations

    def __repr__(self):
        return "Compilation unit with {} declarations".format(
            len(self.declarations)
        )
