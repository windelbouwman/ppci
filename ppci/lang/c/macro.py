""" Preprocessor macros.
"""


class BaseMacro:
    """ Base macro """

    def __init__(self, name, protected=False):
        self.name = name
        self.protected = protected


class Macro(BaseMacro):
    """ Macro define """

    def __init__(
        self, name, value, args=None, protected=False, variadic=False
    ):
        super().__init__(name, protected=protected)
        self.value = value
        self.args = args
        self.variadic = variadic


class FunctionMacro(BaseMacro):
    """ Special macro, like __FILE__ """

    def __init__(self, name, function):
        super().__init__(name, protected=True)
        self.function = function
