""" OCaml utility.

Multiple usage possible, for example:

"""

import argparse
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from ..lang.ocaml.cmo import read_file


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser]
)
subparsers = parser.add_subparsers(
    title='commands',
    description='possible commands', dest='command')

disassemble_parser = subparsers.add_parser(
    'disassemble', help='Disassemble OCaml bytecode.')
disassemble_parser.add_argument(
    'cmofile', metavar='bytecode file', type=argparse.FileType('rb'),
    help='OCaml bytecode file to disassemble')

opt_parser = subparsers.add_parser(
    'opt', help='Compile OCaml bytecode to native code')


def ocaml(args=None):
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        if args.command == 'disassemble':
            read_file(args.cmofile)
        else:  # pragma: no cover
            raise NotImplementedError(args.command)


if __name__ == '__main__':
    ocaml()
