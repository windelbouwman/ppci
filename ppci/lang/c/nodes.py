""" Classes for the abstract syntax tree (AST) nodes for the C language.

The goal is to be able to recreate source from this ast as close to
the original source as possible.
"""


class CompilationUnit:
    """ A single compilation unit """
    def __init__(self, declarations):
        self.declarations = declarations

    def __repr__(self):
        return 'Compilation unit with {} declarations'.format(
            len(self.declarations))


class DeclSpec:
    """ Contains a type and a set of modifiers """
    def __init__(self, storage_class, typ):
        self.storage_class = storage_class
        self.typ = typ  # The later determined type!

    def __repr__(self):
        return '[decl-spec storage={}, type={}]'.format(
            self.storage_class, self.typ)


class Declarator:
    def __init__(self, name, type_modifiers, location):
        self.name = name
        self.type_modifiers = type_modifiers
        self.location = location
