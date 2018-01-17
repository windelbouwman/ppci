""" Build utility.

Use this to execute build files.
"""


import argparse
from .base import base_parser, LogSetup
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser])
parser.add_argument(
    '-f', '--buildfile', metavar='build-file',
    help='use buildfile, otherwise build.xml is the default',
    default='build.xml')
parser.add_argument('targets', metavar='target', nargs='*')


def build(args=None):
    """ Run the build command from command line. Used by ppci-build.py """
    args = parser.parse_args(args)
    with LogSetup(args):
        api.construct(args.buildfile, args.targets)


if __name__ == '__main__':
    build()
