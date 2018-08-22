
class SymbolSet:
    """ Ordered series of ranges """
    def __init__(self, symbols):
        self._symbols = symbols

    def __contains__(self, item):
        return item in self._symbols

