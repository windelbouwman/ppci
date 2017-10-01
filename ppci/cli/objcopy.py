""" Objcopy utility to manipulate object files. """


import argparse
from .base import base_parser, LogSetup
from .. import api
from ..binutils.objectfile import ObjectFile


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser])
parser.add_argument(
    'input', help='input file', type=argparse.FileType('r'))
parser.add_argument(
    '--segment', '-S', help='segment to copy', required=True)
parser.add_argument(
    'output', help='output file')
parser.add_argument(
    '--output-format', '-O', help='output file format')


def objcopy(args=None):
    """ Copy from binary format 1 to binary format 2 """
    args = parser.parse_args(args)
    with LogSetup(args):
        # Read object from file:
        obj = ObjectFile.load(args.input)
        args.input.close()
        api.objcopy(obj, args.segment, args.output_format, args.output)


if __name__ == '__main__':
    objcopy()
