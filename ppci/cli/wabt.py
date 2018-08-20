""" Wasm binary toolkit (WABT)

"""


import argparse
import sys
from .base import base_parser, LogSetup
from ..wasm import read_wat, read_wasm


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser])
subparsers = parser.add_subparsers(
    title='commands',
    description='possible commands', dest='command')

wat2wasm_parser = subparsers.add_parser(
    'wat2wasm', help='Convert binary wasm to wasm text (WAT) format.')
wat2wasm_parser.add_argument(
    'wat', metavar='wat file', type=argparse.FileType('r'),
    help='wasm text file to read')
wat2wasm_parser.add_argument(
    '-o', '--output', metavar='wasm file', type=argparse.FileType('wb'),
    help='File to write the binary wasm file to, default is stdout')

wasm2wat_parser = subparsers.add_parser(
    'wasm2wat', help='Convert binary wasm to wasm text (WAT) format.')
wasm2wat_parser.add_argument(
    'wasm', metavar='wasm file', type=argparse.FileType('rb'),
    help='wasm file to read')
wasm2wat_parser.add_argument(
    '-o', '--output', metavar='wat file', type=argparse.FileType('w'),
    default=sys.stdout,
    help='File to write the WAT file to, default is stdout')


def wabt(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args):
        if args.command == 'wat2wasm':
            wasm_module = read_wat(args.wat)
            wasm_module.to_file(args.output)
            args.output.close()
        elif args.command == 'wasm2wat':
            wasm_module = read_wasm(args.wasm)
            args.output.write(wasm_module.to_string())
            args.output.close()
        else:  # pragma: no cover
            raise NotImplementedError(args.command)


if __name__ == '__main__':
    wabt()
