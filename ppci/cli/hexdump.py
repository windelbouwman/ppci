""" Display file contents in hexadecimal """

import argparse
from .base import base_parser, LogSetup
from ..utils.hexdump import hexdump as dump


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser])
parser.add_argument(
    'file', metavar='file', type=argparse.FileType('rb'),
    help='File to dump contents of')


def hexdump(args=None):
    """ Display file contents in hexadecimal """
    args = parser.parse_args(args)
    with LogSetup(args):
        contents = args.file.read()
        args.file.close()
        dump(contents)


if __name__ == '__main__':
    hexdump()
