
class COptions:
    """ A collection of settings regarding the C language """
    def __init__(self):
        self.settings = {}

    def enable(self, setting):
        self.settings[setting] = True
