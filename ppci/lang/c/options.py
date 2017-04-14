
class COptions:
    """ A collection of settings regarding the C language """
    def __init__(self):
        self.settings = {}
        self.set('trigraphs', False)

    def enable(self, setting):
        self.settings[setting] = True

    def disable(self, setting):
        self.settings[setting] = False

    def set(self, setting, value):
        self.settings[setting] = value

    def __getitem__(self, index):
        return self.settings[index]
