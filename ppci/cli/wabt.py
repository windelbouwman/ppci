""" Wasm binary toolkit (WABT)

"""


import argparse
import sys
from .base import base_parser, LogSetup
from ..wasm import read_wat, read_wasm, execute_wasm


parser = argparse.ArgumentParser(description=__doc__, parents=[base_parser])
subparsers = parser.add_subparsers(
    title="commands", description="possible commands", dest="command"
)

wat2wasm_parser = subparsers.add_parser(
    "wat2wasm", help="Convert binary wasm to wasm text (WAT) format."
)
wat2wasm_parser.add_argument(
    "wat",
    metavar="wat file",
    type=argparse.FileType("r"),
    help="wasm text file to read",
)
wat2wasm_parser.add_argument(
    "-o",
    "--output",
    metavar="wasm file",
    type=argparse.FileType("wb"),
    help="File to write the binary wasm file to, default is stdout",
)

wasm2wat_parser = subparsers.add_parser(
    "wasm2wat", help="Convert binary wasm to wasm text (WAT) format."
)
wasm2wat_parser.add_argument(
    "wasm",
    metavar="wasm file",
    type=argparse.FileType("rb"),
    help="wasm file to read",
)
wasm2wat_parser.add_argument(
    "-o",
    "--output",
    metavar="wat file",
    type=argparse.FileType("w"),
    default=sys.stdout,
    help="File to write the WAT file to, default is stdout",
)

show_interface_parser = subparsers.add_parser(
    "show_interface", help="Load a wasm file and show its interface."
)
show_interface_parser.add_argument(
    "wasm",
    metavar="wasm file",
    type=argparse.FileType("rb"),
    help="wasm file to read",
)

run_parser = subparsers.add_parser("run", help="Execute a wasm file.")
run_parser.add_argument(
    "wasm",
    metavar="wasm file",
    type=argparse.FileType("rb"),
    help="wasm file to read",
)
run_parser.add_argument(
    "--arg",
    dest="wasm_arguments",
    metavar="arg",
    action="append",
    type=int,
    help="Argument to wasm function",
)
run_parser.add_argument(
    "--target",
    dest="wasm_target",
    metavar="target",
    help="Which target to generate code for",
    choices=("native", "python"),
    default="python",
)
run_parser.add_argument(
    "--function",
    "-f",
    dest="wasm_function",
    metavar="function_name",
    help="Function to run",
)


def wabt(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        if args.command == "wat2wasm":
            wasm_module = read_wat(args.wat)
            wasm_module.to_file(args.output)
            args.output.close()
        elif args.command == "wasm2wat":
            wasm_module = read_wasm(args.wasm)
            args.output.write(wasm_module.to_string())
            args.output.close()
        elif args.command == "show_interface":
            wasm_module = read_wasm(args.wasm)
            wasm_module.show_interface()
        elif args.command == "run":
            wasm_module = read_wasm(args.wasm)
            execute_wasm(
                wasm_module,
                args.wasm_arguments,
                target=args.wasm_target,
                function=args.wasm_function,
                reporter=log_setup.reporter
            )
        else:  # pragma: no cover
            parser.print_usage()
            sys.exit(1)


if __name__ == "__main__":
    wabt()
