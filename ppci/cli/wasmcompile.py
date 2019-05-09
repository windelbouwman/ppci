""" Static web assembly compiler.

This command line tool takes web assembly to native code.
"""


import argparse
from .base import base_parser, march_parser
from .base import LogSetup, get_arch_from_args
from .compile_base import compile_parser, do_compile
from ..wasm import read_wasm, wasm_to_ir


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser, march_parser, compile_parser]
)
parser.add_argument(
    "wasm_file",
    metavar="wasm file",
    type=argparse.FileType("rb"),
    help="wasm file to compile",
)


def wasmcompile(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        march = get_arch_from_args(args)
        wasm_module = read_wasm(args.wasm_file)
        args.wasm_file.close()
        ir_module = wasm_to_ir(
            wasm_module,
            march.info.get_type_info("ptr"),
            reporter=log_setup.reporter,
        )

        do_compile([ir_module], march, log_setup.reporter, log_setup.args)


if __name__ == "__main__":
    wasmcompile()
