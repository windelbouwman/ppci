""" Linker.

Use the linker to combine several object files and a memory layout
to produce another resulting object file with images.
"""

import argparse
from .base import base_parser, out_parser, LogSetup
from .. import api


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=__doc__, parents=[base_parser, out_parser])
parser.add_argument(
    'obj', type=argparse.FileType('r'), nargs='+',
    help='the object to link')
parser.add_argument(
    '--layout', '-L', help='memory layout', default=None,
    type=argparse.FileType('r'), metavar='layout-file')
parser.add_argument(
    '-g', help='retain debug information', action='store_true', default=False)


def link(args=None):
    """ Run asm from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        obj = api.link(args.obj, layout=args.layout, debug=args.g)
        obj.save(args.output)
        args.output.close()


if __name__ == '__main__':
    link()
