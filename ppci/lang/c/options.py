from argparse import ArgumentParser


class COptions:
    """ A collection of settings regarding the C language """
    def __init__(self):
        self.settings = {}
        self.include_directories = []

        # Initialize defaults:
        self.disable('trigraphs')
        self.set('std', 'c99')

        # TODO: temporal default paths:
        # self.add_include_path('/usr/include')
        # self.add_include_path(
        #    '/usr/lib/gcc/x86_64-pc-linux-gnu/6.3.1/include/')

        # TODO: handle current directory
        # self.add_include_path('.')

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

    def process_args(self, args):
        """ Given a set of parsed arguments, apply those """
        self.set('trigraphs', args.trigraphs)
        self.set('std', args.std)
        for path in args.I:
            self.add_include_path(path)


# Construct an argument parser for the various C options:
coptions_parser = ArgumentParser(add_help=False)

coptions_parser.add_argument(
    '-I', action='append', default=[], metavar='dir',
    help="Add directory to the include path")

coptions_parser.add_argument(
    '--trigraphs', action="store_true", default=False,
    help="Enable trigraph processing")

coptions_parser.add_argument(
    '--std', choices=('c89', 'c99'), default='c99',
    help="The C version you want to use")
