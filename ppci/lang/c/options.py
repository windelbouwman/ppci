
class COptions:
    """ A collection of settings regarding the C language """
    def __init__(self):
        self.settings = {}
        self.include_directories = []

        # Initialize defaults:
        self.set('trigraphs', False)

        # TODO: temporal default paths:
        self.add_include_path('/usr/include')
        self.add_include_path(
            '/usr/lib/gcc/x86_64-pc-linux-gnu/6.3.1/include/')

        # TODO: handle current directory
        self.add_include_path('.')

    def add_include_path(self, path):
        """ Add a path to the list of include paths """
        self.include_directories.append(path)

    def enable(self, setting):
        self.settings[setting] = True

    def disable(self, setting):
        self.settings[setting] = False

    def set(self, setting, value):
        self.settings[setting] = value

    def __getitem__(self, index):
        return self.settings[index]
