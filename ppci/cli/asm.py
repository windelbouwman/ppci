""" Assembler utility. """


import argparse
from .base import base_parser, march_parser, out_parser, LogSetup
from .base import get_arch_from_args
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser, march_parser, out_parser])
parser.add_argument(
    '-g', '--debug', help='create debug information',
    action='store_true', default=False)
parser.add_argument(
    'sourcefile', type=argparse.FileType('r'),
    help='the source file to assemble')


def asm(args=None):
    """ Run asm from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        # Assemble source:
        march = get_arch_from_args(args)
        obj = api.asm(args.sourcefile, march, debug=args.debug)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


if __name__ == '__main__':
    asm()
