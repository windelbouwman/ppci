""" The different objects which can be declared. """

# pylint: disable=R0903


from .types import CType


class CDeclaration:
    """ A single declaration """
    def __init__(self, storage_class, typ: CType, name, location):
        assert isinstance(typ, CType)
        assert isinstance(name, str) or name is None
        self.name = name
        self.location = location
        self.typ = typ
        self.storage_class = storage_class

    @property
    def is_function(self):
        return isinstance(self, FunctionDeclaration)


class Typedef(CDeclaration):
    """ Type definition """
    def __init__(self, typ, name, location):
        super().__init__('typedef', typ, name, location)

    def __repr__(self):
        return 'Typedef {}'.format(self.name)


class VariableDeclaration(CDeclaration):
    """ Variable declaration, be it local or global """
    def __init__(self, storage_class, typ, name, initial_value, location):
        super().__init__(storage_class, typ, name, location)
        self.initial_value = initial_value

    def __repr__(self):
        return 'Variable [storage={} typ={} name={}]'.format(
            self.storage_class, self.typ, self.name)


class ConstantDeclaration(CDeclaration):
    def __init__(self, storage_class, typ, name, value, location):
        super().__init__(storage_class, typ, name, location)
        self.value = value

    def __repr__(self):
        return 'Constant [typ={} name={}, {}]'.format(
            self.typ, self.name, self.value)


class EnumDeclaration(CDeclaration):
    def __init__(self, constants, location):
        super().__init__(location)
        self.constants = constants


class EnumConstantDeclaration(CDeclaration):
    """ Declaration of an enum value """
    def __init__(self, typ, name, value, location):
        super().__init__(None, typ, name, location)
        self.value = value

    def __repr__(self):
        return 'Value [typ={} name={}, {}]'.format(
            self.typ, self.name, self.value)


class ParameterDeclaration(CDeclaration):
    """ Function parameter declaration """
    def __repr__(self):
        return 'Parameter [typ={} name={}]'.format(
            self.typ, self.name)


class FunctionDeclaration(CDeclaration):
    """ A function declaration """
    def __init__(self, storage_class, typ, name, location):
        super().__init__(storage_class, typ, name, location)
        self.body = None

    def __repr__(self):
        return 'Function storage={} typ={} name={}'.format(
            self.storage_class, self.typ, self.name)
