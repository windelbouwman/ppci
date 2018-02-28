""" Convert binary wasm to wasm text (WAT) format.

"""


import argparse
import sys
from .base import base_parser, LogSetup
from ..wasm import read_wasm


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser])
parser.add_argument(
    'wasm', metavar='wasm file', type=argparse.FileType('rb'),
    help='wasm file to read')
parser.add_argument(
    '-o', '--output', metavar='wat file', type=argparse.FileType('w'),
    default=sys.stdout,
    help='File to write the WAT file to, default is stdout')


def wasm2wat(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args):
        wasm_module = read_wasm(args.wasm)
        args.output.write(wasm_module.to_string())
        args.output.close()


if __name__ == '__main__':
    wasm2wat()
