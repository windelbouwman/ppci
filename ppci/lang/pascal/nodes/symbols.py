""" Symbol AST nodes.

Examples:
- Variables
- parameters
- local variables
- constants and named types.
"""


class Symbol:
    """ Symbol is the base class for all named things like variables,
        functions, constants and types and modules """

    def __init__(self, name: str, typ):
        self.name = name
        self.typ = typ

    @property
    def is_subroutine(self):
        return isinstance(self, SubRoutine)


class Program(Symbol):
    """ A module contains functions, types, consts and global variables """

    def __init__(self, name, inner_scope, location):
        super().__init__(name, None)
        self.location = location
        self.imports = []
        self.inner_scope = inner_scope

    @property
    def types(self):
        """ Get the types in this module """
        return self.inner_scope.types

    @property
    def constants(self):
        """ Get the constants in this module """
        return self.inner_scope.constants

    @property
    def variables(self):
        """ Get the variables in this module """
        return self.inner_scope.variables

    @property
    def functions(self):
        """ Get all the functions that are defined in this module """
        return self.inner_scope.functions

    def __repr__(self):
        return "Program {}".format(self.name)


# duplicates DefinedType?
# class NamedType(Symbol):
#     """ Some types are named, for example a user defined type (typedef)
#         and built in types.
#     """

#     def __init__(self, name, typ):
#         super().__init__(name)
#         self.typ = typ


class DefinedType(Symbol):
    """ A named type indicating another type """

    def __init__(self, name, typ, loc):
        assert isinstance(name, str)
        super().__init__(name, typ)
        self.loc = loc

    def __repr__(self):
        return '"{0}" -> "{1}"'.format(self.name, self.typ)


class Constant(Symbol):
    """ Constant definition """

    def __init__(self, name, typ, value, location):
        super().__init__(name, typ)
        self.value = value
        self.location = location

    def __repr__(self):
        return "CONSTANT {0} = {1}".format(self.name, self.value)


class Variable(Symbol):
    """ A variable, either global or local """

    def __init__(self, name: str, typ, initial_value, location):
        super().__init__(name, typ)
        # assert isinstance(typ)
        self.initial_value = initial_value
        self.isLocal = False
        self.isParameter = False
        self.location = location
        self.ival = None

    def __repr__(self):
        return "Var {} [{}]".format(self.name, self.typ)


class EnumValue(Symbol):
    def __init__(self, name: str, typ, value, location):
        super().__init__(name, typ)
        self.value = value
        self.location = location

    def __repr__(self):
        return "enum-value({})".format(self.value)


class FormalParameter(Variable):
    def __init__(self, name: str, typ, loc):
        super().__init__(name, typ, None, loc)
        self.isParameter = True


class BuiltIn(Symbol):
    def __init__(self, name, typ):
        super().__init__(name, typ)


# Procedure types
class SubRoutine(Symbol):
    @property
    def is_function(self):
        return isinstance(self, Function)

    @property
    def is_procedure(self):
        return isinstance(self, Procedure)


class Function(SubRoutine):
    """ Actual implementation of a function """

    def __init__(self, name: str, location):
        super().__init__(name, None)
        self.location = location

    def __repr__(self):
        return "Func {}".format(self.name)


class Procedure(SubRoutine):
    """ Actual implementation of a function """

    def __init__(self, name: str, location):
        super().__init__(name, None)
        self.location = location

    def __repr__(self):
        return "Func {}".format(self.name)


class RecordFieldProxy(Symbol):
    def __init__(self, name: str, typ, location):
        super().__init__(name, typ)
        self.location = location
