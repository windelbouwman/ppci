""" Convert binary wasm to wasm text (WAT) format.

"""


import argparse
from .base import base_parser, LogSetup
from ..wasm import read_wat


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser])
parser.add_argument(
    'wat', metavar='wat file', type=argparse.FileType('r'),
    help='wasm text file to read')
parser.add_argument(
    '-o', '--output', metavar='wasm file', type=argparse.FileType('wb'),
    help='File to write the binary wasm file to, default is stdout')


def wat2wasm(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args):
        wasm_module = read_wat(args.wat)
        wasm_module.to_file(args.output)
        args.output.close()


if __name__ == '__main__':
    wat2wasm()
