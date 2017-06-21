""" The different objects which can be declared. """

from .types import CType


class Declaration:
    """ A single declaration """
    def __init__(self, typ: CType, name, location):
        assert isinstance(typ, CType)
        assert isinstance(name, str) or name is None
        self.name = name
        self.location = location
        self.typ = typ
        self.storage_class = None

    @property
    def is_function(self):
        return isinstance(self, FunctionDeclaration)


class Typedef(Declaration):
    """ Type definition """
    def __repr__(self):
        return 'Typedef {}'.format(self.name)


class VariableDeclaration(Declaration):
    """ Variable declaration, be it local or global """
    def __init__(self, typ, name, initial_value, loc):
        super().__init__(typ, name, loc)
        self.initial_value = initial_value

    def __repr__(self):
        return 'Variable [typ={} name={}, {}]'.format(
            self.typ, self.name, self.storage_class)


class ConstantDeclaration(Declaration):
    def __init__(self, typ, name, value, loc):
        super().__init__(typ, name, loc)
        self.value = value

    def __repr__(self):
        return 'Constant [typ={} name={}, {}]'.format(
            self.typ, self.name, self.value)


class ValueDeclaration(Declaration):
    """ Declaration of an enum value """
    def __init__(self, typ, name, value, loc):
        super().__init__(typ, name, loc)
        assert isinstance(value, int)
        self.value = value

    def __repr__(self):
        return 'Value [typ={} name={}, {}]'.format(
            self.typ, self.name, self.value)


class ParameterDeclaration(Declaration):
    """ Function parameter declaration """
    def __repr__(self):
        return 'Parameter [typ={} name={}]'.format(
            self.typ, self.name)


class FunctionDeclaration(Declaration):
    """ A function declaration """
    def __init__(self, typ, name, loc):
        super().__init__(typ, name, loc)
        self.body = None

    def __repr__(self):
        return 'FunctionDeclaration typ={} name={}'.format(
            self.typ, self.name)
