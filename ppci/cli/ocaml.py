""" OCaml utility.

Multiple usage possible, for example:

"""

import argparse
import sys
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from ..lang.ocaml import read_file, ocaml_to_ir


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser],
)
subparsers = parser.add_subparsers(
    title="commands", description="possible commands", dest="command"
)

disassemble_parser = subparsers.add_parser(
    "disassemble", help="Disassemble OCaml bytecode."
)
disassemble_parser.add_argument(
    "bytefile",
    metavar="bytecode-file",
    type=argparse.FileType("rb"),
    help="OCaml bytecode file to disassemble",
)

opt_parser = subparsers.add_parser(
    "opt",
    help="Compile OCaml bytecode to native code",
    parents=[march_parser, compile_parser],
)
opt_parser.add_argument(
    "bytefile",
    metavar="bytecode-file",
    type=argparse.FileType("rb"),
    help="OCaml bytecode file to disassemble",
)


def ocaml(args=None):
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        if args.command == "disassemble":
            module = read_file(args.bytefile)
            instructions = module["CODE"]
            for instruction in instructions:
                print(instruction)
        elif args.command == "opt":
            march = get_arch_from_args(args)
            module = read_file(args.bytefile)
            # TODO: implement this?
            ir_modules = [ocaml_to_ir(module)]
            do_compile(ir_modules, march, log_setup.reporter, args)
        else:  # pragma: no cover
            parser.print_usage()
            sys.exit(1)


if __name__ == "__main__":
    ocaml()
