""" C scoping functions """
from .declarations import Declaration


class Scope:
    """ A variable scope """
    def __init__(self, parent=None):
        self.parent = parent
        # Different namespaces in this scope:
        self.var_map = {}
        self.tags = {}
        self.labels = {}

    def is_defined(self, name, all_scopes=True):
        """ Check if the name is defined """
        if name in self.var_map:
            return True
        elif self.parent and all_scopes:
            return self.parent.is_defined(name)
        else:
            return False

    def insert(self, variable: Declaration):
        """ Insert a variable into the current scope """
        assert isinstance(variable, Declaration)
        assert variable.name not in self.var_map
        self.var_map[variable.name] = variable

    def has_tag(self, name):
        if self.parent:
            # TODO: make tags a flat space?
            return self.parent.has_tag(name)
        return name in self.tags

    def get_tag(self, name):
        """ Get a struct by tag """
        if self.parent:
            return self.parent.get_tag(name)
        return self.tags[name]

    def add_tag(self, name, o):
        if self.parent:
            return self.parent.add_tag(name, o)
        self.tags[name] = o

    def get(self, name):
        """ Get the symbol with the given name """
        if name in self.var_map:
            return self.var_map[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise KeyError(name)
